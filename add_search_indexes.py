#!/usr/bin/env python3
"""
Add search performance indexes to the database.
This script adds missing indexes for LIKE operations used in search queries.
"""

import asyncio
import logging
from libs.common.database import DatabaseManager
from libs.common.config import get_settings
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def add_search_indexes():
    """Add indexes to improve search performance"""
    
    indexes_to_create = [
        "CREATE INDEX IF NOT EXISTS idx_content_title ON content_items(title);",
        "CREATE INDEX IF NOT EXISTS idx_content_summary ON content_items(summary);", 
        "CREATE INDEX IF NOT EXISTS idx_content_sports_keywords ON content_items(sports_keywords);",
        "CREATE INDEX IF NOT EXISTS idx_content_content_type ON content_items(content_type);",
        "CREATE INDEX IF NOT EXISTS idx_content_active_quality ON content_items(is_active, quality_score);",
        "CREATE INDEX IF NOT EXISTS idx_content_published_quality ON content_items(published_at, quality_score);"
    ]
    
    settings = get_settings()
    db_manager = DatabaseManager(settings.database.url)
    
    session_gen = db_manager.get_session()
    session = await session_gen.__anext__()
    
    try:
        logger.info("Adding search performance indexes...")
        
        for index_sql in indexes_to_create:
            logger.info(f"Creating index: {index_sql}")
            await session.execute(text(index_sql))
            
        await session.commit()
        logger.info("Successfully added all search indexes")
        
    except Exception as e:
        logger.error(f"Error adding indexes: {e}")
        await session.rollback()
        raise
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(add_search_indexes())