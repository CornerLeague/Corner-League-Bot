#!/usr/bin/env python3
"""
Simple test script to manually crawl one article and add it to the database
"""

import asyncio
import logging
from datetime import datetime

from libs.common.config import get_settings
from libs.common.database import ConnectionPool, DatabaseManager
from libs.ingestion.crawler import WebCrawler
from libs.ingestion.extractor import ContentExtractor
from libs.quality.scorer import QualityGate

# Content storage is handled directly via database models

# Configure logging
logging.basicConfig(level=logging.INFO)
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
                await session.flush()  # Get the ID

            # Create content hash
            content_text = content_item.get("text_content", "")
            content_hash = hashlib.sha256(content_text.encode()).hexdigest()

            # Check if content already exists
            existing = await session.execute(
                select(ContentItem).where(ContentItem.canonical_url == content_item["canonical_url"])
            )
            existing_item = existing.scalar_one_or_none()

            if existing_item:
                logger.info(f"Content already exists: {existing_item.id}")
                return existing_item.id

            # Create new content item
            new_item = ContentItem(
                id=str(uuid.uuid4()),
                source_id=source.id,
                original_url=content_item["canonical_url"],
                canonical_url=content_item["canonical_url"],
                content_hash=content_hash,
                title=content_item["title"],
                text=content_item.get("text_content", ""),
                byline=content_item.get("byline"),
                summary=content_item.get("summary"),
                published_at=content_item.get("published_at"),
                language=content_item.get("language", "en"),
                word_count=content_item.get("word_count", 0),
                image_url=content_item.get("image_url"),
                sports_keywords=content_item.get("sports_keywords", []),
                content_type=content_item.get("content_type", "article"),
                quality_score=content_item.get("quality_score", 0.5),
                is_active=True,
                is_duplicate=False,
                is_spam=False
            )

            session.add(new_item)
            await session.commit()

            logger.info(f"Stored content item: {new_item.id}")
            return new_item.id

    except Exception as e:
        logger.error(f"Failed to store content: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_single_article():
    """Test crawling a single article"""

    settings = get_settings()

    # Initialize components
    db_manager = DatabaseManager(settings.database.url)
    connection_pool = ConnectionPool(settings.database.url, max_connections=5)

    try:
        # Initialize database
        await db_manager.initialize()
        await connection_pool.initialize()

        # Initialize crawler
        crawler = WebCrawler(settings)
        await crawler.initialize()

        # Initialize other components
        extractor = ContentExtractor(settings)
        quality_gate = QualityGate(settings)
        # Content storage handled via database models

        # Test URL - ESPN article
        test_url = "https://www.espn.com/mlb/story/_/id/39500000/mlb-news-latest"

        logger.info(f"Testing crawl of: {test_url}")

        # Crawl the article
        crawl_result = await crawler.crawl_url(test_url)

        if not crawl_result or crawl_result.get("status_code") != 200:
            logger.error(f"Failed to crawl {test_url}")
            return

        logger.info(f"Successfully crawled {test_url}")

        # Extract content
        extraction_result = extractor.extract_content(
            crawl_result["content"],
            test_url
        )

        if not extraction_result:
            logger.error(f"Failed to extract content from {test_url}")
            return

        logger.info(f"Successfully extracted content: {extraction_result.get('title', 'No title')}")

        # Check quality
        quality_result = await quality_gate.assess_quality(extraction_result)

        if not quality_result or not quality_result.get("passes_quality_gate", False):
            logger.warning(f"Content failed quality check: {quality_result}")
            return

        logger.info(f"Content passed quality check with score: {quality_result.get('quality_score', 0)}")

        # Store content
        content_item = {
            "title": extraction_result.get("title", "Test Article"),
            "byline": extraction_result.get("byline"),
            "summary": extraction_result.get("summary"),
            "canonical_url": test_url,
            "published_at": extraction_result.get("published_at") or datetime.now(),
            "quality_score": quality_result.get("quality_score", 0.5),
            "sports_keywords": extraction_result.get("sports_keywords", []),
            "content_type": "article",
            "image_url": extraction_result.get("image_url"),
            "word_count": extraction_result.get("word_count"),
            "language": "en",
            "source_domain": "espn.com",
            "text_content": extraction_result.get("text_content", "")
        }

        stored_id = await store_content_item(content_item, db_manager)

        if stored_id:
            logger.info(f"Successfully stored article with ID: {stored_id}")
            print(f"\n✅ SUCCESS: Article stored with ID {stored_id}")
            print(f"Title: {content_item['title']}")
            print(f"Quality Score: {content_item['quality_score']}")
            print(f"Sports Keywords: {content_item['sports_keywords']}")
        else:
            logger.error("Failed to store article")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        if "crawler" in locals():
            await crawler.close()
        if "connection_pool" in locals():
            await connection_pool.close()
        if "db_manager" in locals():
            await db_manager.close()

if __name__ == "__main__":
    asyncio.run(test_single_article())
