#!/usr/bin/env python3
"""
Script to clear test data from the database and prepare for real crawled content.
"""

import asyncio
import logging
from sqlalchemy import text
from libs.common.database import DatabaseManager
from libs.common.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def clear_test_data():
    """Clear all test data from the database."""
    settings = get_settings()
    db_manager = DatabaseManager(settings.database.url)
    
    try:
        async for session in db_manager.get_session():
            logger.info("Clearing test data from database...")
            
            # Get current counts
            result = await session.execute(
                text("SELECT COUNT(*) FROM content_items")
            )
            content_count = result.scalar()
            
            result = await session.execute(
                text("SELECT COUNT(*) FROM trending_terms")
            )
            trending_count = result.scalar()
            
            result = await session.execute(
                text("SELECT COUNT(*) FROM sources")
            )
            source_count = result.scalar()
            
            logger.info(f"Current data: {content_count} articles, {trending_count} trending terms, {source_count} sources")
            
            # Clear content items and related data
            await session.execute(text("DELETE FROM user_interactions"))
            await session.execute(text("DELETE FROM quality_signals"))
            await session.execute(text("DELETE FROM content_items"))
            await session.execute(text("DELETE FROM trending_terms"))
            await session.execute(text("DELETE FROM ingestion_jobs"))
            
            # Keep sources but reset their crawl status
            await session.execute(
                text("UPDATE sources SET last_crawled = NULL, success_rate = 1.0")
            )
            
            await session.commit()
            logger.info("✅ Test data cleared successfully")
            
    except Exception as e:
        logger.error(f"❌ Error clearing test data: {e}")
        raise
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(clear_test_data())