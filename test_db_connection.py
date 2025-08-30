import asyncpg
import asyncio

async def test_connection():
    try:
        conn = await asyncpg.connect('postgresql://sports_user:sports_pass@localhost:5434/sportsdb')
        print('Connected successfully!')
        result = await conn.fetchval('SELECT current_user')
        print(f'Current user: {result}')
        await conn.close()
    except Exception as e:
        print(f'Connection failed: {e}')

if __name__ == '__main__':
    asyncio.run(test_connection())
