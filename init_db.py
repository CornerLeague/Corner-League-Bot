#!/usr/bin/env python3

import asyncio

from libs.common.config import get_settings
from libs.common.database import DatabaseManager


async def main():
    settings = get_settings()
    db_manager = DatabaseManager(settings.database.url)

    print("Creating database tables...")
    await db_manager.create_tables()
    print("Database tables created successfully!")

if __name__ == "__main__":
    asyncio.run(main())
