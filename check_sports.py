import asyncio

from sqlalchemy import select

from libs.common.database import get_db_session
from libs.common.questionnaire_models import Sport


async def check_sports():
    async with get_db_session() as db:
        result = await db.execute(select(Sport))
        sports = result.scalars().all()
        print(f"Total sports: {len(sports)}")
        for sport in sports:
            print(f"- {sport.name} (active: {sport.is_active})")

if __name__ == "__main__":
    asyncio.run(check_sports())
