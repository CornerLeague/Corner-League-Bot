# Copyright (c) 2024 Sports Media Platform
# Licensed under the MIT License

"""
Crawler worker for continuous content discovery and ingestion.
Implements security, monitoring, and operational excellence.
"""

import asyncio
import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import aioredis
from pydantic import BaseModel

from libs.common.config import get_settings, Settings
from libs.common.database import ConnectionPool
from libs.ingestion.crawler import WebCrawler, CrawlerGuardrails
from libs.ingestion.extractor import ContentExtractor, CanonicalURLExtractor, DuplicateDetector
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
        
        # Components
        self.connection_pool: Optional[ConnectionPool] = None
        self.redis_client: Optional[aioredis.Redis] = None
        self.crawler: Optional[WebCrawler] = None
        self.extractor: Optional[ContentExtractor] = None
        self.quality_gate: Optional[QualityGate] = None
        self.trending_loop: Optional[TrendingDiscoveryLoop] = None
        
        # Statistics
        self.stats = WorkerStats(
            worker_id=worker_id,
            start_time=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )
        
        # Performance tracking
        self.crawl_times: List[float] = []
        self.extraction_times: List[float] = []
        
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
            self.redis_client = aioredis.from_url(
                self.settings.redis.url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Redis client initialized")
            
            # Initialize crawler with guardrails
            guardrails = CrawlerGuardrails(self.settings)
            self.crawler = WebCrawler(self.settings, guardrails)
            await self.crawler.initialize()
            logger.info("Web crawler initialized")
            
            # Initialize content extractor
            canonical_extractor = CanonicalURLExtractor()
            duplicate_detector = DuplicateDetector(self.redis_client)
            self.extractor = ContentExtractor(
                self.settings, 
                canonical_extractor, 
                duplicate_detector
            )
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
            "pid": str(os.getpid()) if 'os' in globals() else "unknown"
        }
        
        await self.redis_client.hset(worker_key, mapping=worker_data)
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
                    await asyncio.sleep(self.settings.crawler.cycle_delay_seconds)
                
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
            batch_size = self.settings.crawler.batch_size
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
    
    async def _get_crawl_urls(self) -> List[str]:
        """Get URLs to crawl from discovery sources"""
        
        urls = []
        
        try:
            # Get URLs from RSS feeds
            rss_urls = await self._get_rss_urls()
            urls.extend(rss_urls)
            
            # Get URLs from search discovery
            search_urls = await self._get_search_discovery_urls()
            urls.extend(search_urls)
            
            # Get URLs from sitemap discovery
            sitemap_urls = await self._get_sitemap_urls()
            urls.extend(sitemap_urls)
            
            # Remove duplicates and limit
            unique_urls = list(set(urls))
            return unique_urls[:self.settings.crawler.max_urls_per_cycle]
        
        except Exception as e:
            logger.error(f"Error getting crawl URLs: {e}")
            return []
    
    async def _get_rss_urls(self) -> List[str]:
        """Get URLs from RSS feed monitoring"""
        
        try:
            # Get active RSS feeds from database
            query = """
            SELECT url, last_crawled 
            FROM rss_feeds 
            WHERE is_active = true 
            AND (last_crawled IS NULL OR last_crawled < NOW() - INTERVAL '1 hour')
            ORDER BY priority DESC, last_crawled ASC NULLS FIRST
            LIMIT 50
            """
            
            rows = await self.connection_pool.fetch(query)
            
            urls = []
            for row in rows:
                feed_url = row['url']
                
                # Parse RSS feed and extract article URLs
                feed_urls = await self.crawler.parse_rss_feed(feed_url)
                urls.extend(feed_urls)
                
                # Update last crawled timestamp
                await self.connection_pool.execute(
                    "UPDATE rss_feeds SET last_crawled = NOW() WHERE url = $1",
                    feed_url
                )
            
            return urls
        
        except Exception as e:
            logger.error(f"Error getting RSS URLs: {e}")
            return []
    
    async def _get_search_discovery_urls(self) -> List[str]:
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
    
    async def _get_sitemap_urls(self) -> List[str]:
        """Get URLs from sitemap discovery"""
        
        try:
            # Get sources that need sitemap crawling
            query = """
            SELECT domain, sitemap_url, last_sitemap_crawl
            FROM sources 
            WHERE is_active = true 
            AND sitemap_url IS NOT NULL
            AND (last_sitemap_crawl IS NULL OR last_sitemap_crawl < NOW() - INTERVAL '6 hours')
            ORDER BY priority DESC, last_sitemap_crawl ASC NULLS FIRST
            LIMIT 10
            """
            
            rows = await self.connection_pool.fetch(query)
            
            urls = []
            for row in rows:
                sitemap_url = row['sitemap_url']
                
                # Parse sitemap and extract URLs
                sitemap_urls = await self.crawler.parse_sitemap(sitemap_url)
                urls.extend(sitemap_urls)
                
                # Update last crawled timestamp
                await self.connection_pool.execute(
                    "UPDATE sources SET last_sitemap_crawl = NOW() WHERE domain = $1",
                    row['domain']
                )
            
            return urls
        
        except Exception as e:
            logger.error(f"Error getting sitemap URLs: {e}")
            return []
    
    async def _process_url_batch(self, urls: List[str]):
        """Process a batch of URLs"""
        
        tasks = []
        for url in urls:
            task = asyncio.create_task(self._process_single_url(url))
            tasks.append(task)
        
        # Process with concurrency limit
        semaphore = asyncio.Semaphore(self.settings.crawler.max_concurrent_requests)
        
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
            if not crawl_result.success:
                return
            
            crawl_time = (time.time() - crawl_start) * 1000
            self.crawl_times.append(crawl_time)
            self.stats.pages_crawled += 1
            
            # Step 2: Extract content
            extraction_start = time.time()
            
            extraction_result = await self.extractor.extract_content(
                crawl_result.html,
                url,
                crawl_result.final_url
            )
            
            if not extraction_result.success:
                return
            
            extraction_time = (time.time() - extraction_start) * 1000
            self.extraction_times.append(extraction_time)
            
            # Step 3: Check for duplicates
            is_duplicate = await self.extractor.duplicate_detector.is_duplicate(
                extraction_result.content_hash,
                extraction_result.canonical_url
            )
            
            if is_duplicate:
                self.stats.duplicates_filtered += 1
                return
            
            # Step 4: Quality assessment
            quality_score = await self.quality_gate.assess_quality(extraction_result)
            
            if not self.quality_gate.passes_threshold(quality_score):
                self.stats.quality_filtered += 1
                return
            
            # Step 5: Store content
            await self._store_content(extraction_result, quality_score)
            self.stats.content_extracted += 1
            
            # Update statistics
            self._update_performance_stats()
        
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            self.stats.errors += 1
    
    async def _store_content(self, extraction_result, quality_score: float):
        """Store extracted content in database"""
        
        try:
            # Get or create source
            source_id = await self._get_or_create_source(extraction_result.source_domain)
            
            # Insert content item
            query = """
            INSERT INTO content_items (
                id, title, byline, text, summary, canonical_url, original_url,
                published_at, quality_score, sports_keywords, content_type,
                image_url, source_id, word_count, language, content_hash,
                created_at, updated_at, is_active
            ) VALUES (
                gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15, NOW(), NOW(), true
            )
            ON CONFLICT (canonical_url) DO UPDATE SET
                updated_at = NOW(),
                quality_score = EXCLUDED.quality_score
            """
            
            await self.connection_pool.execute(
                query,
                extraction_result.title,
                extraction_result.byline,
                extraction_result.text,
                extraction_result.summary,
                extraction_result.canonical_url,
                extraction_result.original_url,
                extraction_result.published_at,
                quality_score,
                extraction_result.sports_keywords,
                extraction_result.content_type,
                extraction_result.image_url,
                source_id,
                extraction_result.word_count,
                extraction_result.language,
                extraction_result.content_hash
            )
        
        except Exception as e:
            logger.error(f"Error storing content: {e}")
            raise
    
    async def _get_or_create_source(self, domain: str) -> str:
        """Get or create source record"""
        
        try:
            # Try to get existing source
            source_id = await self.connection_pool.fetchval(
                "SELECT id FROM sources WHERE domain = $1",
                domain
            )
            
            if source_id:
                return source_id
            
            # Create new source
            source_id = await self.connection_pool.fetchval("""
                INSERT INTO sources (id, domain, name, is_active, created_at, updated_at)
                VALUES (gen_random_uuid(), $1, $2, true, NOW(), NOW())
                RETURNING id
            """, domain, domain.replace('www.', '').title())
            
            return source_id
        
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
        
        self.stats.last_heartbeat = datetime.utcnow()
        
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
        
        await self.redis_client.hset(worker_key, mapping=worker_data)
        await self.redis_client.expire(worker_key, 300)  # 5 minute TTL
    
    async def _trending_discovery_loop(self):
        """Run trending discovery in background"""
        
        while self.running and not self.shutdown_requested:
            try:
                await self.trending_loop.run_discovery_cycle()
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
                await self.crawler.close()
            
            if self.connection_pool:
                await self.connection_pool.close()
            
            if self.redis_client:
                await self.redis_client.close()
        
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
    worker_id = os.getenv('WORKER_ID', f"crawler-{int(time.time())}")
    
    # Load settings
    settings = get_settings()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format=f'%(asctime)s - {worker_id} - %(name)s - %(levelname)s - %(message)s'
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

