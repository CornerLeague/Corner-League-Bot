#!/usr/bin/env python3

import asyncio
import uuid
from sqlalchemy import select
from libs.common.database import get_db
from libs.common.questionnaire_models import Sport

async def test_sport_validation():
    """Test sport ID validation with different formats."""

    # Test sport IDs from the error message
    test_sport_ids = [
        'c4476633-3ee4-40c5-9c06-a719751175cb',
        '6433e8ef-84ed-48eb-8fc5-80bd939bc32d',
        '7cbde06d-91a8-4993-95c1-fe4ecd635459',
        '6343bb43-8001-413e-a010-cd78070da3df'
    ]

    # Use the same approach as the API
    async for db in get_db():
        print("Testing sport ID validation...")
        print("=" * 50)

        # Test 1: Query with string UUIDs (what the API currently does)
        print("\n1. Testing with string UUIDs:")
        sports_stmt = select(Sport).where(Sport.id.in_(test_sport_ids), Sport.is_active == True)
        result = await db.execute(sports_stmt)
        existing_sports = result.scalars().all()
        print(f"Found {len(existing_sports)} sports with string UUIDs")
        for sport in existing_sports:
            print(f"  - {sport.name} ({sport.id})")

        # Test 2: Query with UUID objects
        print("\n2. Testing with UUID objects:")
        uuid_objects = [uuid.UUID(sport_id) for sport_id in test_sport_ids]
        sports_stmt = select(Sport).where(Sport.id.in_(uuid_objects), Sport.is_active == True)
        result = await db.execute(sports_stmt)
        existing_sports = result.scalars().all()
        print(f"Found {len(existing_sports)} sports with UUID objects")
        for sport in existing_sports:
            print(f"  - {sport.name} ({sport.id})")

        # Test 3: Query all active sports to see their actual IDs
        print("\n3. All active sports in database:")
        all_sports_stmt = select(Sport).where(Sport.is_active == True)
        result = await db.execute(all_sports_stmt)
        all_sports = result.scalars().all()
        print(f"Total active sports: {len(all_sports)}")
        for sport in all_sports:
            print(f"  - {sport.name}: {sport.id} (type: {type(sport.id)})")
            if str(sport.id) in test_sport_ids:
                print(f"    ✓ MATCHES test ID: {str(sport.id)}")

        break  # Only use the first database session

if __name__ == "__main__":
    asyncio.run(test_sport_validation())
