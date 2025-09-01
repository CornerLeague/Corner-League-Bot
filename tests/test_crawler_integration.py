#!/usr/bin/env python3
"""
Integrated crawler test suite.
Consolidates crawler testing for single article crawling, fresh crawler instances, and updated crawler functionality.
"""

import asyncio
import logging
from datetime import datetime

from apps.workers.crawler_worker import CrawlerWorker
from libs.common.config import get_settings
from libs.common.database import ConnectionPool, DatabaseManager
from libs.ingestion.crawler import WebCrawler
from libs.ingestion.extractor import ContentExtractor
from libs.quality.scorer import QualityGate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def store_content_item(content_item, db_manager):
    """Store content item in database"""
    import hashlib
    import uuid
    from urllib.parse import urlparse

    from sqlalchemy import select

    from libs.common.database import ContentItem, Source

    try:
        async with db_manager.get_session() as session:
            # Get or create source
            domain = urlparse(content_item["canonical_url"]).netloc

            # Check if source exists
            source_result = await session.execute(
                select(Source).where(Source.domain == domain)
            )
            source = source_result.scalar_one_or_none()

            if not source:
                # Create new source
                source = Source(
                    id=str(uuid.uuid4()),
                    name=domain.replace("www.", "").title(),
                    domain=domain,
                    base_url=f"https://{domain}",
                    is_active=True
                )
                session.add(source)
                await session.flush()

            # Create content hash for deduplication
            content_hash = hashlib.sha256(
                content_item["content"].encode("utf-8")
            ).hexdigest()

            # Check if content already exists
            existing_result = await session.execute(
                select(ContentItem).where(ContentItem.content_hash == content_hash)
            )
            existing_content = existing_result.scalar_one_or_none()

            if existing_content:
                logger.info(f"Content already exists: {content_item['title']}")
                return existing_content.id

            # Create new content item
            content_db_item = ContentItem(
                id=str(uuid.uuid4()),
                source_id=source.id,
                title=content_item["title"],
                content=content_item["content"],
                summary=content_item.get("summary", ""),
                canonical_url=content_item["canonical_url"],
                published_at=content_item.get("published_at"),
                author=content_item.get("author"),
                content_hash=content_hash,
                quality_score=content_item.get("quality_score", 0.0),
                relevance_score=content_item.get("relevance_score", 0.0),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            session.add(content_db_item)
            await session.commit()

            logger.info(f"Stored content: {content_item['title']}")
            return content_db_item.id

    except Exception as e:
        logger.error(f"Error storing content: {e}")
        await session.rollback()
        raise


async def test_single_article():
    """Test crawling and processing a single article"""
    logger.info("Testing single article crawling...")

    settings = get_settings()
    db_manager = DatabaseManager(settings)

    try:
        await db_manager.initialize()

        # Test URL - using a reliable sports news source
        test_url = "https://www.espn.com/nba/story/_/id/39234567/nba-news-latest"

        # Initialize components
        crawler = WebCrawler(settings)
        extractor = ContentExtractor()
        quality_gate = QualityGate()

        logger.info(f"Crawling URL: {test_url}")

        # Crawl the page
        raw_content = await crawler.crawl_url(test_url)

        if not raw_content:
            logger.error("Failed to crawl content")
            return False

        logger.info(f"Raw content length: {len(raw_content)} characters")

        # Extract structured content
        extracted_content = await extractor.extract_content(test_url, raw_content)

        if not extracted_content:
            logger.error("Failed to extract content")
            return False

        logger.info(f"Extracted title: {extracted_content.get('title', 'N/A')}")

        # Apply quality scoring
        quality_score = quality_gate.score_content(extracted_content)
        extracted_content["quality_score"] = quality_score

        logger.info(f"Quality score: {quality_score}")

        # Store in database
        content_id = await store_content_item(extracted_content, db_manager)

        if content_id:
            logger.info(f"✅ Single article test PASSED - Content stored with ID: {content_id}")
            return True
        else:
            logger.error("❌ Single article test FAILED - Could not store content")
            return False

    except Exception as e:
        logger.error(f"❌ Single article test FAILED - Error: {e}")
        return False
    finally:
        await db_manager.close()


async def test_fresh_crawler():
    """Test a fresh crawler instance with RSS-only configuration"""
    logger.info("Testing fresh crawler instance...")

    settings = get_settings()
    worker_id = f"test-crawler-{int(asyncio.get_event_loop().time())}"

    # Create a fresh crawler worker
    worker = CrawlerWorker(worker_id, settings)

    try:
        await worker.initialize()

        # Test URL discovery
        logger.info("Testing URL discovery...")
        urls = await worker._get_crawl_urls()

        if not urls:
            logger.error("❌ Fresh crawler test FAILED - No URLs discovered")
            return False

        logger.info(f"Discovered {len(urls)} URLs")

        # Test processing a few URLs
        test_urls = urls[:3]  # Test first 3 URLs
        processed_count = 0

        for url in test_urls:
            try:
                logger.info(f"Testing URL: {url}")
                result = await worker._process_url(url)
                if result:
                    processed_count += 1
                    logger.info(f"Successfully processed: {url}")
            except Exception as e:
                logger.warning(f"Failed to process {url}: {e}")

        if processed_count > 0:
            logger.info(f"✅ Fresh crawler test PASSED - Processed {processed_count}/{len(test_urls)} URLs")
            return True
        else:
            logger.error("❌ Fresh crawler test FAILED - No URLs processed successfully")
            return False

    except Exception as e:
        logger.error(f"❌ Fresh crawler test FAILED - Error: {e}")
        return False
    finally:
        await worker.cleanup()


async def test_updated_crawler():
    """Test the updated crawler with RSS-only configuration"""
    logger.info("Testing updated crawler with RSS-only configuration...")

    settings = get_settings()

    async with WebCrawler(settings) as crawler:
        # Test source config with both RSS and sitemap URLs
        source_config = {
            "rss_url": "https://bleacherreport.com/articles/feed",
            "sitemap_url": "https://www.si.com/sitemap.xml"  # This should be ignored
        }

        try:
            # Test RSS URL discovery (should ignore sitemap)
            logger.info("Testing RSS-only URL discovery...")
            urls = await crawler.discover_urls_from_source(source_config)

            if not urls:
                logger.error("❌ Updated crawler test FAILED - No URLs discovered from RSS")
                return False

            logger.info(f"Discovered {len(urls)} URLs from RSS feed")

            # Verify that only RSS URLs are used (not sitemap)
            rss_only = all("bleacherreport.com" in url for url in urls[:5])  # Check first 5

            if rss_only:
                logger.info("✅ Updated crawler test PASSED - RSS-only mode working correctly")
                return True
            else:
                logger.error("❌ Updated crawler test FAILED - Non-RSS URLs found")
                return False

        except Exception as e:
            logger.error(f"❌ Updated crawler test FAILED - Error: {e}")
            return False


async def run_all_crawler_tests():
    """Run all crawler tests"""
    print("Running Integrated Crawler Tests")
    print("=" * 40)
    print()

    results = []

    # Run individual tests
    logger.info("1. Testing single article crawling...")
    results.append(await test_single_article())
    print()

    logger.info("2. Testing fresh crawler instance...")
    results.append(await test_fresh_crawler())
    print()

    logger.info("3. Testing updated crawler RSS-only mode...")
    results.append(await test_updated_crawler())
    print()

    # Summary
    print("\nTest Summary:")
    print("=" * 20)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All crawler tests PASSED!")
        return True
    else:
        print(f"\n❌ {total - passed} crawler test(s) FAILED")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_crawler_tests())
    exit(0 if success else 1)
