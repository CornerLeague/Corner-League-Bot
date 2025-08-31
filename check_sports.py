#!/usr/bin/env python3
import asyncio
from libs.common.database import ConnectionPool
from libs.common.config import Settings

async def check_sports():
    settings = Settings()
    db = ConnectionPool(settings.database.url)
    await db.initialize()

    sports = await db.fetch('SELECT id, name, slug, is_active FROM sports ORDER BY display_order')
    print('Available sports:')
    for sport in sports:
        print(f'  ID: {sport["id"]}, Name: {sport["name"]}, Slug: {sport["slug"]}, Active: {sport["is_active"]}')

    await db.close()

if __name__ == "__main__":
    asyncio.run(check_sports())
