#!/usr/bin/env python3
import asyncio
from libs.common.database import ConnectionPool
from libs.common.config import Settings

async def check_users():
    settings = Settings()
    # Fix the database URL for asyncpg
    db_url = settings.database.url.replace('postgresql+asyncpg://', 'postgresql://')
    pool = ConnectionPool(db_url)
    await pool.initialize()

    try:
        users = await pool.fetch('SELECT user_id, email, favorite_teams FROM users LIMIT 5')
        print('Users in database:')
        for user in users:
            print(f"  - {user['email']} (ID: {user['user_id']}) - Teams: {user['favorite_teams']}")

        if not users:
            print('No users found in database')

    except Exception as e:
        print(f'Error: {e}')
    finally:
        await pool.close()

if __name__ == '__main__':
    asyncio.run(check_users())
