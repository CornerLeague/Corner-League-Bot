# Copyright (c) 2024 Sports Media Platform
# Licensed under the MIT License

"""
Crawler worker for continuous content discovery and ingestion.
Implements security, monitoring, and operational excellence.
"""

import asyncio
import logging
import os
import signal
import sys
import time
from datetime import datetime

from pydantic import BaseModel
from redis.asyncio import Redis

from libs.common.config import Settings, get_settings
from libs.common.database import ConnectionPool
from libs.common.test_user_config import (
    calculate_relevance_score,
    get_dodgers_filter_config,
    get_test_user_config,
    is_dodgers_relevant_content,
)
from libs.ingestion.crawler import WebCrawler
from libs.ingestion.extractor import ContentExtractor, NearDuplicateDetector, URLCanonicalizer
from libs.quality.scorer import QualityGate
from libs.search.trending import TrendingDiscoveryLoop

logger = logging.getLogger(__name__)


class WorkerStats(BaseModel):
    """Worker statistics model"""

    worker_id: str
    start_time: datetime
    last_heartbeat: datetime
    pages_crawled: int = 0
    content_extracted: int = 0
    duplicates_filtered: int = 0
    quality_filtered: int = 0
    errors: int = 0
    avg_crawl_time_ms: float = 0.0
    avg_extraction_time_ms: float = 0.0
    current_status: str = "idle"
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0


class CrawlerWorker:
    """Production crawler worker with comprehensive monitoring and security"""

    def __init__(self, worker_id: str, settings: Settings):
        self.worker_id = worker_id
        self.settings = settings
        self.running = False
        self.shutdown_requested = False

        # User preferences for content filtering
        self.test_user_config = get_test_user_config()
        self.dodgers_filter_config = get_dodgers_filter_config()

        # Components
        self.connection_pool: ConnectionPool | None = None
        self.redis_client: Redis | None = None
        self.crawler: WebCrawler | None = None
        self.extractor: ContentExtractor | None = None
        self.quality_gate: QualityGate | None = None
        self.trending_loop: TrendingDiscoveryLoop | None = None

        # Statistics
        self.stats = WorkerStats(
            worker_id=worker_id,
            start_time=datetime.now(),
            last_heartbeat=datetime.now()
        )

        # Performance tracking
        self.crawl_times: list[float] = []
        self.extraction_times: list[float] = []

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Worker {self.worker_id} received signal {signum}, initiating graceful shutdown")
        self.shutdown_requested = True

    async def initialize(self):
        """Initialize worker components"""

        logger.info(f"Initializing crawler worker {self.worker_id}")

        try:
            # Initialize database connection pool
            self.connection_pool = ConnectionPool(self.settings.database.url)
            await self.connection_pool.initialize()
            logger.info("Database connection pool initialized")

            # Initialize Redis client
            self.redis_client = await Redis.from_url(
                self.settings.redis.url,
                encoding="utf-8"
            )
            await self.redis_client.ping()
            logger.info("Redis client initialized")

            # Initialize crawler
            self.crawler = WebCrawler(self.settings)
            self.crawler = await self.crawler.__aenter__()
            logger.info("Web crawler initialized")

            # Initialize content extractor
            canonical_extractor = URLCanonicalizer()
            duplicate_detector = NearDuplicateDetector()
            self.extractor = ContentExtractor()
            logger.info("Content extractor initialized")

            # Initialize quality gate
            self.quality_gate = QualityGate(self.settings)
            logger.info("Quality gate initialized")

            # Initialize trending discovery loop
            self.trending_loop = TrendingDiscoveryLoop(self.settings, self.connection_pool)
            logger.info("Trending discovery loop initialized")

            # Register worker in Redis
            await self._register_worker()

            logger.info(f"Crawler worker {self.worker_id} initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize worker {self.worker_id}: {e}")
            raise

    async def _register_worker(self):
        """Register worker in Redis for monitoring"""

        worker_key = f"worker:{self.worker_id}"
        worker_data = {
            "worker_id": self.worker_id,
            "start_time": self.stats.start_time.isoformat(),
            "status": "initializing",
            "pid": str(os.getpid()) if "os" in globals() else "unknown"
        }

        # Set each field individually for Redis compatibility
        for field, value in worker_data.items():
            await self.redis_client.hset(worker_key, field, value)
        await self.redis_client.expire(worker_key, 300)  # 5 minute TTL

    async def run(self):
        """Main worker loop"""

        self.running = True
        self.stats.current_status = "running"

        logger.info(f"Starting crawler worker {self.worker_id}")

        try:
            # Start heartbeat task
            heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            # Start trending discovery task
            trending_task = asyncio.create_task(self._trending_discovery_loop())

            # Main crawling loop
            while self.running and not self.shutdown_requested:
                try:
                    await self._crawl_cycle()

                    # Brief pause between cycles
                    await asyncio.sleep(30)  # Default 30 seconds between cycles

                except Exception as e:
                    logger.error(f"Error in crawl cycle: {e}")
                    self.stats.errors += 1

                    # Exponential backoff on errors
                    await asyncio.sleep(min(60, 2 ** min(self.stats.errors, 6)))

            # Cancel background tasks
            heartbeat_task.cancel()
            trending_task.cancel()

            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

            try:
                await trending_task
            except asyncio.CancelledError:
                pass

        except Exception as e:
            logger.error(f"Fatal error in worker {self.worker_id}: {e}")
            raise

        finally:
            await self._cleanup()

    async def _crawl_cycle(self):
        """Single crawling cycle"""

        cycle_start = time.time()
        self.stats.current_status = "crawling"

        try:
            # Get URLs to crawl from discovery queue
            urls_to_crawl = await self._get_crawl_urls()

            if not urls_to_crawl:
                self.stats.current_status = "idle"
                return

            logger.info(f"Worker {self.worker_id} crawling {len(urls_to_crawl)} URLs")

            # Process URLs in batches
            batch_size = 10  # Hardcoded batch size for now
            for i in range(0, len(urls_to_crawl), batch_size):
                batch = urls_to_crawl[i:i + batch_size]
                await self._process_url_batch(batch)

                # Check for shutdown between batches
                if self.shutdown_requested:
                    break

            cycle_time = (time.time() - cycle_start) * 1000
            logger.info(f"Worker {self.worker_id} completed cycle in {cycle_time:.1f}ms")

        except Exception as e:
            logger.error(f"Error in crawl cycle: {e}")
            raise

        finally:
            self.stats.current_status = "idle"

    async def _get_crawl_urls(self) -> list[str]:
        """Get URLs to crawl from discovery sources - RSS feeds only"""

        urls = []

        try:
            # Get URLs from RSS feeds only - focusing on major sports sources
            rss_urls = await self._get_rss_urls()
            logger.info(f"RSS discovery returned {len(rss_urls)} URLs")
            urls.extend(rss_urls)

            # Disable search discovery to focus only on RSS feeds
            # search_urls = await self._get_search_discovery_urls()
            # logger.info(f"Search discovery returned {len(search_urls)} URLs")
            # urls.extend(search_urls)
            logger.info("Search discovery disabled - using RSS feeds only")

            # Disable sitemap discovery to focus on RSS feeds
            # sitemap_urls = await self._get_sitemap_urls()
            # logger.info(f"Sitemap discovery returned {len(sitemap_urls)} URLs")
            # urls.extend(sitemap_urls)
            logger.info("Sitemap discovery disabled - using RSS feeds only")

            # Remove duplicates and limit
            unique_urls = list(set(urls))
            logger.info(f"Total unique URLs to process: {len(unique_urls)}")

            # Log first few URLs for debugging
            if unique_urls:
                logger.info(f"Sample URLs to crawl: {unique_urls[:3]}")

            return unique_urls[:100]  # Increased limit for better RSS coverage

        except Exception as e:
            logger.error(f"Error getting crawl URLs: {e}")
            return []

    async def get_comprehensive_sports_rss_feeds(self) -> list[str]:
        """Get comprehensive list of sports RSS feeds"""
        return [
            # Major sports news
            "http://rss.cnn.com/rss/edition_sport.rss",
            "https://feeds.bbci.co.uk/sport/rss.xml",
            "https://www.espn.com/espn/rss/news",
            "https://www.si.com/rss/si_topstories.rss",
            "https://bleacherreport.com/articles/feed",
            "https://www.cbssports.com/rss/headlines/",
            "https://sports.yahoo.com/rss/",
            "https://www.foxsports.com/rss/sports",

            # League-specific feeds
            "https://www.nba.com/rss/nba_rss.xml",
            "https://www.nfl.com/feeds/rss/news",
            "https://www.mlb.com/feeds/news/rss.xml",
            "https://www.nhl.com/rss/news",

            # International sports
            "https://www.skysports.com/rss/12040",
            "https://www.goal.com/feeds/en/news",
            "https://www.eurosport.com/rss.xml",

            # College sports
            "https://www.ncaa.com/news/rss.xml",
            "https://www.collegeinsider.com/rss.php",

            # Fantasy and analysis
            "https://www.fantasypros.com/rss/news.xml",
            "https://www.rotowire.com/rss/news.htm"
        ]

    async def _get_rss_urls(self) -> list[str]:
        """Get URLs from RSS feed monitoring"""

        try:
            # Get comprehensive list of sports RSS feeds
            rss_feeds = await self.get_comprehensive_sports_rss_feeds()

            urls = []
            for feed_url in rss_feeds:
                try:
                    # Parse RSS feed and extract article URLs
                    if self.crawler:
                        feed_urls = await self.crawler.discovery_engine.discover_from_rss(feed_url)
                        urls.extend(feed_urls)
                        logger.info(f"Discovered {len(feed_urls)} URLs from {feed_url}")
                except Exception as e:
                    logger.warning(f"Failed to parse RSS feed {feed_url}: {e}")
                    continue

            logger.info(f"Total RSS URLs discovered: {len(urls)}")
            return urls[:50]  # Limit to 50 URLs for better coverage

        except Exception as e:
            logger.error(f"Error getting RSS URLs: {e}")
            return []

    async def _get_search_discovery_urls(self) -> list[str]:
        """Get URLs from search engine discovery"""

        try:
            # Get trending terms for search queries
            trending_terms = await self.trending_loop.detector.detect_trending()

            urls = []
            for term in trending_terms[:10]:  # Limit to top 10 trending terms
                # Generate search queries
                search_queries = [
                    f"{term.term} sports news",
                    f"{term.term} latest update",
                    f"{term.term} breaking news"
                ]

                for query in search_queries:
                    search_urls = await self.crawler.search_discovery(query)
                    urls.extend(search_urls)

            return urls

        except Exception as e:
            logger.error(f"Error getting search discovery URLs: {e}")
            return []

    async def _get_sitemap_urls(self) -> list[str]:
        """Get URLs from sitemap discovery - DISABLED for RSS-only mode"""

        # Sitemap discovery is completely disabled to focus on RSS feeds only
        logger.info("Sitemap discovery is disabled - using RSS feeds only")
        return []

    async def _process_url_batch(self, urls: list[str]):
        """Process a batch of URLs"""

        tasks = []
        for url in urls:
            task = asyncio.create_task(self._process_single_url(url))
            tasks.append(task)

        # Process with concurrency limit
        semaphore = asyncio.Semaphore(5)  # Default concurrent requests limit

        async def process_with_semaphore(task):
            async with semaphore:
                return await task

        results = await asyncio.gather(
            *[process_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )

        # Log results
        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - successful

        logger.info(f"Batch processed: {successful} successful, {failed} failed")

    async def _process_single_url(self, url: str):
        """Process a single URL through the complete pipeline"""

        crawl_start = time.time()

        try:
            # Step 1: Crawl the page
            crawl_result = await self.crawler.crawl_url(url)
            if not crawl_result or crawl_result.get("status_code", 0) >= 400:
                return

            crawl_time = (time.time() - crawl_start) * 1000
            self.crawl_times.append(crawl_time)
            self.stats.pages_crawled += 1

            # Step 2: Extract content
            extraction_start = time.time()

            extraction_result = self.extractor.extract_content(
                crawl_result["content"],
                crawl_result.get("final_url", url)
            )

            if not extraction_result.get("extraction_success", False):
                return

            extraction_time = (time.time() - extraction_start) * 1000
            self.extraction_times.append(extraction_time)

            # Step 3: User preference filtering (Dodgers content)
            is_relevant = is_dodgers_relevant_content(
                extraction_result.get("title", ""),
                extraction_result.get("text", ""),
                extraction_result.get("sports_keywords", [])
            )

            if not is_relevant:
                logger.debug(f"Content not relevant to Dodgers fan: {extraction_result.get('title', '')}")
                return

            # Calculate relevance score for personalization
            relevance_score = calculate_relevance_score(
                extraction_result.get("title", ""),
                extraction_result.get("text", ""),
                extraction_result.get("sports_keywords", []),
                extraction_result.get("content_type")
            )

            # Step 4: Check for duplicates
            is_duplicate = await self.extractor.duplicate_detector.is_duplicate(
                extraction_result.get("content_hash"),
                extraction_result.get("canonical_url")
            )

            if is_duplicate:
                self.stats.duplicates_filtered += 1
                return

            # Step 5: Quality assessment
            # Create source info for quality gate
            source_info = {
                "domain": extraction_result.get("source_domain", "unknown"),
                "name": extraction_result.get("source_name", "Unknown"),
                "quality_tier": 2,  # Default tier
                "reputation_score": 0.7,  # Default reputation
                "success_rate": 0.9  # Default success rate
            }

            quality_result = self.quality_gate.process_content(extraction_result, source_info)

            if not quality_result["should_accept"]:
                self.stats.quality_filtered += 1
                logger.info(f"Content filtered by quality gate: {quality_result['decision_reason']}")
                return

            quality_score = quality_result["quality_result"]["quality_score"]

            # Step 6: Store content
            await self._store_content(extraction_result, quality_score, relevance_score)
            self.stats.content_extracted += 1

            # Update statistics
            self._update_performance_stats()

        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            self.stats.errors += 1

    async def _store_content(self, extraction_result, quality_score: float, relevance_score: float = 0.0):
        """Store extracted content in database"""

        try:
            import uuid
            from urllib.parse import urlparse

            from sqlalchemy import select

            from libs.common.database import ContentItem, DatabaseManager

            # Get or create source
            domain = urlparse(extraction_result.get("canonical_url")).netloc
            source_id = await self._get_or_create_source(domain)

            # Use SQLAlchemy session
            db_manager = DatabaseManager()
            async with db_manager.get_session() as session:
                # Check if content already exists
                existing = await session.execute(
                    select(ContentItem).where(ContentItem.canonical_url == extraction_result.get("canonical_url"))
                )
                existing_item = existing.scalar_one_or_none()

                if existing_item:
                    # Update existing item
                    existing_item.quality_score = quality_score
                    existing_item.relevance_score = relevance_score
                    existing_item.updated_at = datetime.now()
                else:
                    # Create new content item
                    content_item = ContentItem(
                        id=str(uuid.uuid4()),
                        title=extraction_result.get("title"),
                        byline=extraction_result.get("byline"),
                        text=extraction_result.get("text"),
                        summary=extraction_result.get("summary"),
                        canonical_url=extraction_result.get("canonical_url"),
                        original_url=extraction_result.get("url"),
                        published_at=extraction_result.get("published_at"),
                        quality_score=quality_score,
                        relevance_score=relevance_score,
                        sports_keywords=extraction_result.get("sports_keywords", []),
                        content_type=extraction_result.get("content_type"),
                        image_url=extraction_result.get("image_url"),
                        source_id=source_id,
                        word_count=extraction_result.get("word_count", 0),
                        language=extraction_result.get("language"),
                        content_hash=extraction_result.get("content_hash"),
                        is_active=True
                    )
                    session.add(content_item)

                await session.commit()

        except Exception as e:
            logger.error(f"Error storing content: {e}")
            raise

    async def _get_or_create_source(self, domain: str) -> str:
        """Get or create source record"""

        try:
            import uuid

            from sqlalchemy import select

            from libs.common.database import DatabaseManager, Source

            db_manager = DatabaseManager()
            async with db_manager.get_session() as session:
                # Try to get existing source
                result = await session.execute(
                    select(Source).where(Source.domain == domain)
                )
                existing_source = result.scalar_one_or_none()

                if existing_source:
                    return existing_source.id

                # Create new source
                source = Source(
                    id=str(uuid.uuid4()),
                    domain=domain,
                    name=domain.replace("www.", "").title(),
                    is_active=True
                )
                session.add(source)
                await session.commit()

                return source.id

        except Exception as e:
            logger.error(f"Error getting/creating source for {domain}: {e}")
            raise

    def _update_performance_stats(self):
        """Update performance statistics"""

        # Update average crawl time
        if self.crawl_times:
            self.stats.avg_crawl_time_ms = sum(self.crawl_times) / len(self.crawl_times)

            # Keep only recent times (last 100)
            if len(self.crawl_times) > 100:
                self.crawl_times = self.crawl_times[-100:]

        # Update average extraction time
        if self.extraction_times:
            self.stats.avg_extraction_time_ms = sum(self.extraction_times) / len(self.extraction_times)

            # Keep only recent times (last 100)
            if len(self.extraction_times) > 100:
                self.extraction_times = self.extraction_times[-100:]

    async def _heartbeat_loop(self):
        """Send periodic heartbeat to Redis"""

        while self.running and not self.shutdown_requested:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(30)  # Heartbeat every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(30)

    async def _send_heartbeat(self):
        """Send heartbeat with current statistics"""

        self.stats.last_heartbeat = datetime.now()

        # Get system metrics
        try:
            import psutil
            process = psutil.Process()
            self.stats.memory_usage_mb = process.memory_info().rss / 1024 / 1024
            self.stats.cpu_usage_percent = process.cpu_percent()
        except ImportError:
            pass

        # Update worker status in Redis
        worker_key = f"worker:{self.worker_id}"
        worker_data = {
            "last_heartbeat": self.stats.last_heartbeat.isoformat(),
            "status": self.stats.current_status,
            "pages_crawled": str(self.stats.pages_crawled),
            "content_extracted": str(self.stats.content_extracted),
            "duplicates_filtered": str(self.stats.duplicates_filtered),
            "quality_filtered": str(self.stats.quality_filtered),
            "errors": str(self.stats.errors),
            "avg_crawl_time_ms": f"{self.stats.avg_crawl_time_ms:.1f}",
            "avg_extraction_time_ms": f"{self.stats.avg_extraction_time_ms:.1f}",
            "memory_usage_mb": f"{self.stats.memory_usage_mb:.1f}",
            "cpu_usage_percent": f"{self.stats.cpu_usage_percent:.1f}"
        }

        # Set each field individually
        for field, value in worker_data.items():
            await self.redis_client.hset(worker_key, field, value)
        await self.redis_client.expire(worker_key, 300)  # 5 minute TTL

    async def _trending_discovery_loop(self):
        """Run trending discovery in background"""

        while self.running and not self.shutdown_requested:
            try:
                # Simple trending discovery - just detect trending terms
                if self.trending_loop and hasattr(self.trending_loop, "detector"):
                    trending_terms = await self.trending_loop.detector.detect_trending()
                    logger.info(f"Detected {len(trending_terms)} trending terms")
                await asyncio.sleep(300)  # Run every 5 minutes

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in trending discovery loop: {e}")
                await asyncio.sleep(300)

    async def _cleanup(self):
        """Cleanup resources"""

        logger.info(f"Cleaning up worker {self.worker_id}")

        try:
            # Update worker status
            if self.redis_client:
                worker_key = f"worker:{self.worker_id}"
                await self.redis_client.hset(worker_key, "status", "shutdown")
                await self.redis_client.expire(worker_key, 60)  # Keep for 1 minute

            # Close connections
            if self.crawler:
                await self.crawler.__aexit__(None, None, None)

            if self.connection_pool:
                await self.connection_pool.close()

            if self.redis_client:
                await self.redis_client.aclose()

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

        logger.info(f"Worker {self.worker_id} cleanup complete")

    async def stop(self):
        """Stop the worker gracefully"""

        logger.info(f"Stopping worker {self.worker_id}")
        self.running = False
        self.shutdown_requested = True


# Worker management functions
async def start_crawler_worker(worker_id: str, settings: Settings):
    """Start a single crawler worker"""

    worker = CrawlerWorker(worker_id, settings)

    try:
        await worker.initialize()
        await worker.run()

    except Exception as e:
        logger.error(f"Worker {worker_id} failed: {e}")
        raise

    finally:
        await worker.stop()


async def main():
    """Main entry point for crawler worker"""

    import os

    # Get worker ID from environment or generate one
    worker_id = os.getenv("WORKER_ID", f"crawler-{int(time.time())}")

    # Load settings
    settings = get_settings()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format=f"%(asctime)s - {worker_id} - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info(f"Starting crawler worker {worker_id}")

    try:
        await start_crawler_worker(worker_id, settings)

    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down")

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

