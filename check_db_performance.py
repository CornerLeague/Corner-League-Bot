#!/usr/bin/env python3
import asyncio
import time

from sqlalchemy import text

from libs.common.config import get_settings
from libs.common.database import DatabaseManager


async def check_database():
    settings = get_settings()
    db_manager = DatabaseManager(settings.database.url)

    try:
        session = await db_manager.get_session().__anext__()

        # Check total articles
        result = await session.execute(text("SELECT COUNT(*) as count FROM content_items"))
        total_count = result.fetchone()[0]
        print(f"Total articles in database: {total_count}")

        # Check Dodgers articles
        start_time = time.time()
        result = await session.execute(text("SELECT COUNT(*) as count FROM content_items WHERE sports_keywords LIKE '%dodgers%'"))
        dodgers_count = result.fetchone()[0]
        search_time = time.time() - start_time
        print(f"Dodgers articles: {dodgers_count}")
        print(f"Search time: {search_time:.3f} seconds")

        # Check recent articles
        result = await session.execute(text("SELECT COUNT(*) as count FROM content_items WHERE datetime(published_at) > datetime('now', '-7 days')"))
        recent_count = result.fetchone()[0]
        print(f"Recent articles (last 7 days): {recent_count}")

        # Check if there are any active articles
        result = await session.execute(text("SELECT COUNT(*) as count FROM content_items WHERE is_active = 1"))
        active_count = result.fetchone()[0]
        print(f"Active articles: {active_count}")

    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(check_database())
