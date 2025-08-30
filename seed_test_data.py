#!/usr/bin/env python3
"""
Seed the database with test sports content for testing search functionality.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import text

from libs.common.config import get_settings
from libs.common.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test content data
TEST_CONTENT = [
    {
        "title": "Dodgers Win World Series in Dramatic Fashion",
        "summary": "The Los Angeles Dodgers defeated the Yankees 4-1 in the World Series, with Mookie Betts leading the charge with clutch hitting throughout the series.",
        "content": "In a thrilling World Series matchup, the Los Angeles Dodgers captured their second championship in four years by defeating the New York Yankees 4 games to 1. Mookie Betts was named World Series MVP after batting .350 with 3 home runs and 8 RBIs. The Dodgers' pitching staff, led by Walker Buehler and Julio Urías, held the powerful Yankees offense to just 2.1 runs per game over the five-game series.",
        "url": "https://example.com/dodgers-world-series-win",
        "sports_keywords": "dodgers,world series,mookie betts,baseball,mlb,yankees,championship",
        "content_type": "article",
        "source_domain": "espn.com"
    },
    {
        "title": "Lakers Trade Rumors Heat Up Before Deadline",
        "summary": "The Los Angeles Lakers are reportedly exploring trade options to bolster their roster for a playoff push, with several role players mentioned in discussions.",
        "content": "As the NBA trade deadline approaches, the Los Angeles Lakers are actively shopping for improvements to their roster. Sources close to the organization suggest that the team is looking to add depth at the center position and improve their three-point shooting. LeBron James and Anthony Davis have both expressed confidence in the front office's ability to make the right moves.",
        "url": "https://example.com/lakers-trade-rumors",
        "sports_keywords": "lakers,nba,trade deadline,lebron james,anthony davis,basketball",
        "content_type": "article",
        "source_domain": "theathletic.com"
    },
    {
        "title": "Rams Prepare for Playoff Push with Key Additions",
        "summary": "The Los Angeles Rams have made several key acquisitions as they prepare for the NFL playoffs, strengthening both their offensive and defensive units.",
        "content": "The Los Angeles Rams are making final preparations for their playoff run, having recently added veteran linebacker Bobby Wagner and wide receiver Allen Robinson to their roster. Head coach Sean McVay expressed optimism about the team's chances, citing improved chemistry and health across the roster. The Rams' defense has shown significant improvement over the past month.",
        "url": "https://example.com/rams-playoff-preparation",
        "sports_keywords": "rams,nfl,playoffs,sean mcvay,bobby wagner,football",
        "content_type": "article",
        "source_domain": "nfl.com"
    },
    {
        "title": "Kings Make Coaching Change Mid-Season",
        "summary": "The Sacramento Kings have fired their head coach and named an interim replacement as the team struggles to meet expectations this season.",
        "content": "In a surprising move, the Sacramento Kings have parted ways with head coach Mike Brown after a disappointing start to the season. The team has named assistant coach Alvin Gentry as the interim head coach. The Kings currently sit at 15-20 and have struggled with consistency on both ends of the floor. De'Aaron Fox and Domantas Sabonis have both publicly supported the coaching change.",
        "url": "https://example.com/kings-coaching-change",
        "sports_keywords": "kings,nba,coaching change,mike brown,alvin gentry,basketball,sacramento",
        "content_type": "article",
        "source_domain": "bleacherreport.com"
    },
    {
        "title": "Dodgers Sign Star Pitcher to Record Contract",
        "summary": "The Los Angeles Dodgers have signed Japanese pitcher Yoshinobu Yamamoto to a record-breaking 12-year, $325 million contract.",
        "content": "The Los Angeles Dodgers have made the biggest splash of the MLB offseason by signing Japanese ace Yoshinobu Yamamoto to a historic 12-year, $325 million contract. The 25-year-old right-hander was the most coveted free agent pitcher on the market after dominating in Japan's NPB. Yamamoto posted a 1.21 ERA with 176 strikeouts in 164 innings last season. The signing gives the Dodgers one of the most formidable rotations in baseball.",
        "url": "https://example.com/dodgers-yamamoto-signing",
        "sports_keywords": "dodgers,yoshinobu yamamoto,mlb,baseball,free agency,contract,pitcher",
        "content_type": "article",
        "source_domain": "mlb.com"
    },
    {
        "title": "UCLA Basketball Upsets Top-Ranked Duke",
        "summary": "UCLA's basketball team pulled off a stunning upset victory over #1 ranked Duke in a thrilling overtime game at Pauley Pavilion.",
        "content": "In one of the biggest upsets of the college basketball season, UCLA defeated top-ranked Duke 89-87 in overtime at Pauley Pavilion. The Bruins were led by sophomore guard Jaylen Clark, who scored 28 points and grabbed 8 rebounds. The victory snapped Duke's 15-game winning streak and marked UCLA's first win over a #1 ranked team since 2008. The crowd of 13,800 was on their feet for the final 10 minutes of regulation and throughout overtime.",
        "url": "https://example.com/ucla-upsets-duke",
        "sports_keywords": "ucla,duke,college basketball,upset,jaylen clark,pauley pavilion",
        "content_type": "article",
        "source_domain": "espn.com"
    }
]

async def create_test_source(session, domain: str) -> str:
    """Create a test source if it doesn't exist"""
    source_id = str(uuid4())

    # Check if source already exists
    result = await session.execute(
        text("SELECT id FROM sources WHERE domain = :domain"),
        {"domain": domain}
    )
    existing = result.fetchone()

    if existing:
        return existing[0]

    # Create new source
    await session.execute(
        text("""
        INSERT INTO sources (id, name, domain, base_url, source_type, is_active, quality_tier, reputation_score)
        VALUES (:id, :name, :domain, :base_url, :source_type, :is_active, :quality_tier, :reputation_score)
        """),
        {
            "id": source_id,
            "name": domain.replace(".com", "").title(),
            "domain": domain,
            "base_url": f"https://{domain}",
            "source_type": "rss",
            "is_active": True,
            "quality_tier": 1,
            "reputation_score": 0.9
        }
    )

    return source_id

async def seed_database():
    """Seed the database with test content"""
    settings = get_settings()
    db_manager = DatabaseManager(settings.database.url)

    try:
        session = await db_manager.get_session().__anext__()

        logger.info("Seeding database with test sports content...")

        for i, content in enumerate(TEST_CONTENT, 1):
            # Create source if needed
            source_id = await create_test_source(session, content["source_domain"])

            # Create content item
            content_id = str(uuid4())
            published_at = datetime.utcnow() - timedelta(days=i)  # Spread out over recent days

            await session.execute(
                text("""
                INSERT INTO content_items (
                    id, source_id, original_url, canonical_url, content_hash, title, summary, text, content_type,
                    sports_keywords, published_at, is_active, is_duplicate, is_spam,
                    quality_score, created_at, updated_at
                ) VALUES (
                    :id, :source_id, :original_url, :canonical_url, :content_hash, :title, :summary, :text, :content_type,
                    :sports_keywords, :published_at, :is_active, :is_duplicate, :is_spam,
                    :quality_score, :created_at, :updated_at
                )
                """),
                {
                    "id": content_id,
                    "source_id": source_id,
                    "original_url": content["url"],
                        "canonical_url": content["url"],
                        "content_hash": str(hash(content["content"])),
                        "title": content["title"],
                        "summary": content["summary"],
                        "text": content["content"],
                    "content_type": content["content_type"],
                    "sports_keywords": content["sports_keywords"],
                    "published_at": published_at,
                    "is_active": True,
                    "is_duplicate": False,
                    "is_spam": False,
                    "quality_score": 0.85,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            )

            logger.info(f"Added content item {i}: {content['title']}")

        await session.commit()
        logger.info(f"Successfully seeded database with {len(TEST_CONTENT)} test articles")

    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        await session.rollback()
        raise
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
