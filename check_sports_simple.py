#!/usr/bin/env python3
import asyncio
import asyncpg
from libs.common.config import Settings

async def check_sports():
    settings = Settings()
    # Remove the +asyncpg suffix for direct asyncpg connection
    db_url = settings.database.url.replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(db_url)
    try:
        # Query sports
        sports = await conn.fetch("""
            SELECT id, name, slug, is_active
            FROM sports
            ORDER BY name
        """)

        print("Available Sports:")
        print("-" * 80)
        for sport in sports:
            print(f"ID: {sport['id']}")
            print(f"Name: {sport['name']}")
            print(f"Slug: {sport['slug']}")
            print(f"Active: {sport['is_active']}")
            print("-" * 40)

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_sports())
