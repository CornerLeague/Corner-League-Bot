#!/usr/bin/env python3
"""
Database seeding script for Sports Media Platform.
Seeds the database with initial data for development and testing.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta

from libs.common.config import Settings
from libs.common.database import ConnectionPool

logger = logging.getLogger(__name__)


async def seed_sources(connection_pool: ConnectionPool) -> list[str]:
    """Seed initial sports media sources"""

    sources = [
        # Major Sports Publishers
        {
            "domain": "espn.com",
            "name": "ESPN",
            "is_active": True,
            "source_type": "major_publisher",
            "rss_feeds": [
                "https://www.espn.com/espn/rss/news",
                "https://www.espn.com/espn/rss/nba/news",
                "https://www.espn.com/espn/rss/nfl/news",
                "https://www.espn.com/espn/rss/mlb/news"
            ]
        },
        {
            "domain": "si.com",
            "name": "Sports Illustrated",
            "is_active": True,
            "source_type": "major_publisher",
            "rss_feeds": [
                "https://www.si.com/rss/si_topstories.rss"
            ]
        },
        {
            "domain": "theathletic.com",
            "name": "The Athletic",
            "is_active": True,
            "source_type": "major_publisher",
            "rss_feeds": []
        },
        {
            "domain": "cbssports.com",
            "name": "CBS Sports",
            "is_active": True,
            "source_type": "major_publisher",
            "rss_feeds": [
                "https://www.cbssports.com/rss/headlines"
            ]
        },
        {
            "domain": "foxsports.com",
            "name": "Fox Sports",
            "is_active": True,
            "source_type": "major_publisher",
            "rss_feeds": []
        },

        # Team Official Sites
        {
            "domain": "nba.com",
            "name": "NBA Official",
            "is_active": True,
            "source_type": "league_official",
            "rss_feeds": [
                "https://www.nba.com/news/rss.xml"
            ]
        },
        {
            "domain": "nfl.com",
            "name": "NFL Official",
            "is_active": True,
            "source_type": "league_official",
            "rss_feeds": [
                "https://www.nfl.com/news/rss.xml"
            ]
        },
        {
            "domain": "mlb.com",
            "name": "MLB Official",
            "is_active": True,
            "source_type": "league_official",
            "rss_feeds": [
                "https://www.mlb.com/news/rss.xml"
            ]
        },

        # Sports Blogs
        {
            "domain": "sbnation.com",
            "name": "SB Nation",
            "is_active": True,
            "source_type": "sports_blog",
            "rss_feeds": [
                "https://www.sbnation.com/rss/index.xml"
            ]
        },
        {
            "domain": "bleacherreport.com",
            "name": "Bleacher Report",
            "is_active": True,
            "source_type": "sports_blog",
            "rss_feeds": [
                "https://bleacherreport.com/articles.rss"
            ]
        },

        # Regional Sports Media
        {
            "domain": "latimes.com",
            "name": "LA Times Sports",
            "is_active": True,
            "source_type": "regional_media",
            "rss_feeds": []
        },
        {
            "domain": "boston.com",
            "name": "Boston.com Sports",
            "is_active": True,
            "source_type": "regional_media",
            "rss_feeds": []
        }
    ]

    source_ids = []

    for source_data in sources:
        # Insert source
        source_id = await connection_pool.fetchval("""
            INSERT INTO sources (
                id, domain, name, base_url, is_active, source_type,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), $1, $2, $3, $4, $5, NOW(), NOW()
            )
            ON CONFLICT (domain) DO UPDATE SET
                name = EXCLUDED.name,
                base_url = EXCLUDED.base_url,
                is_active = EXCLUDED.is_active,
                source_type = EXCLUDED.source_type,
                updated_at = NOW()
            RETURNING id
        """,
            source_data["domain"],
            source_data["name"],
            source_data.get("base_url", f"https://{source_data['domain']}"),
            source_data["is_active"],
            source_data["source_type"]
        )

        source_ids.append(source_id)

        # Update source with primary RSS feed if available
        if source_data["rss_feeds"]:
            primary_rss_url = source_data["rss_feeds"][0]  # Use first RSS feed as primary
            await connection_pool.execute("""
                UPDATE sources
                SET rss_url = $1, updated_at = NOW()
                WHERE id = $2
            """, primary_rss_url, source_id)

    logger.info(f"Seeded {len(sources)} sources with RSS feeds")
    return source_ids


async def seed_sample_content(connection_pool: ConnectionPool, source_ids: list[str]):
    """Seed sample content items for testing"""

    sample_articles = [
        {
            "title": "Lakers Defeat Warriors in Overtime Thriller",
            "byline": "ESPN Staff",
            "text": "In a thrilling overtime battle at Crypto.com Arena, the Los Angeles Lakers defeated the Golden State Warriors 128-125. LeBron James led the Lakers with 35 points, 8 rebounds, and 12 assists in what many are calling one of the games of the season. The victory moves the Lakers to 25-15 on the season and strengthens their position in the Western Conference playoff race.",
            "summary": "Lakers beat Warriors 128-125 in overtime with LeBron James scoring 35 points.",
            "canonical_url": "https://espn.com/nba/story/lakers-warriors-overtime-thriller",
            "original_url": "https://espn.com/nba/story/lakers-warriors-overtime-thriller",
            "published_at": datetime.utcnow() - timedelta(hours=2),
            "quality_score": 0.92,
            "sports_keywords": ["Lakers", "Warriors", "NBA", "LeBron James", "overtime"],
            "content_type": "game_recap",
            "word_count": 156,
            "language": "en"
        },
        {
            "title": "NFL Draft Prospects: Top 10 Quarterbacks to Watch",
            "byline": "Sports Illustrated",
            "text": "As the NFL Draft approaches, quarterback prospects are generating significant buzz among scouts and analysts. Leading the pack is Caleb Williams from USC, whose combination of arm strength and mobility has impressed evaluators. Drake Maye from North Carolina and Jayden Daniels from LSU round out the top three in most draft boards. This quarterback class is considered one of the strongest in recent years.",
            "summary": "Analysis of top NFL Draft quarterback prospects led by Caleb Williams, Drake Maye, and Jayden Daniels.",
            "canonical_url": "https://si.com/nfl/draft-prospects-quarterbacks-2024",
            "original_url": "https://si.com/nfl/draft-prospects-quarterbacks-2024",
            "published_at": datetime.utcnow() - timedelta(hours=6),
            "quality_score": 0.88,
            "sports_keywords": ["NFL", "Draft", "quarterbacks", "Caleb Williams", "Drake Maye"],
            "content_type": "analysis",
            "word_count": 134,
            "language": "en"
        },
        {
            "title": "World Series Preview: Dodgers vs Yankees",
            "byline": "CBS Sports",
            "text": "The stage is set for a classic World Series matchup between the Los Angeles Dodgers and New York Yankees. Both teams finished with over 100 wins during the regular season and have looked dominant throughout the playoffs. The Dodgers boast the best offense in baseball, while the Yankees counter with exceptional pitching depth. Game 1 is scheduled for Friday night at Yankee Stadium.",
            "summary": "World Series preview between the 100-win Dodgers and Yankees, starting Friday at Yankee Stadium.",
            "canonical_url": "https://cbssports.com/mlb/world-series-preview-dodgers-yankees",
            "original_url": "https://cbssports.com/mlb/world-series-preview-dodgers-yankees",
            "published_at": datetime.utcnow() - timedelta(hours=12),
            "quality_score": 0.85,
            "sports_keywords": ["MLB", "World Series", "Dodgers", "Yankees", "playoffs"],
            "content_type": "preview",
            "word_count": 118,
            "language": "en"
        },
        {
            "title": "Trade Deadline Recap: Major Moves Across the League",
            "byline": "The Athletic",
            "text": "The NBA trade deadline delivered several blockbuster moves that could reshape the playoff picture. The Phoenix Suns acquired Bradley Beal from Washington in exchange for multiple first-round picks and young players. Meanwhile, the Miami Heat bolster their frontcourt by trading for Kristaps Porzingis. These moves signal an arms race among contending teams as the playoffs approach.",
            "summary": "NBA trade deadline recap featuring Bradley Beal to Phoenix and Kristaps Porzingis to Miami.",
            "canonical_url": "https://theathletic.com/nba/trade-deadline-recap-major-moves",
            "original_url": "https://theathletic.com/nba/trade-deadline-recap-major-moves",
            "published_at": datetime.utcnow() - timedelta(days=1),
            "quality_score": 0.90,
            "sports_keywords": ["NBA", "trade deadline", "Bradley Beal", "Kristaps Porzingis", "playoffs"],
            "content_type": "news",
            "word_count": 142,
            "language": "en"
        }
    ]

    for i, article in enumerate(sample_articles):
        source_id = source_ids[i % len(source_ids)]

        await connection_pool.execute("""
            INSERT INTO content_items (
                id, title, byline, text, summary, canonical_url, original_url,
                published_at, quality_score, sports_keywords, content_type,
                source_id, word_count, language, content_hash,
                created_at, updated_at, is_active
            ) VALUES (
                gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, $12, $13, $14, NOW(), NOW(), true
            )
            ON CONFLICT (canonical_url) DO NOTHING
        """,
            article["title"],
            article["byline"],
            article["text"],
            article["summary"],
            article["canonical_url"],
            article["original_url"],
            article["published_at"],
            article["quality_score"],
            json.dumps(article["sports_keywords"]),
            article["content_type"],
            source_id,
            article["word_count"],
            article["language"],
            f"hash_{i}"  # Simple hash for demo
        )

    logger.info(f"Seeded {len(sample_articles)} sample content items")


async def seed_users(connection_pool: ConnectionPool):
    """Seed sample users for testing"""

    users = [
        {
            "email": "admin@sportsmedia.com",
            "username": "admin",
            "full_name": "Admin User",
            "is_active": True,
            "favorite_teams": ["Lakers", "Dodgers", "Rams"],
            "favorite_sports": ["basketball", "baseball", "football"]
        },
        {
            "email": "editor@sportsmedia.com",
            "username": "editor",
            "full_name": "Editor User",
            "is_active": True,
            "favorite_teams": ["Warriors", "Giants", "49ers"],
            "favorite_sports": ["basketball", "baseball", "football"]
        },
        {
            "email": "user@sportsmedia.com",
            "username": "testuser",
            "full_name": "Test User",
            "is_active": True,
            "favorite_teams": ["Celtics", "Patriots", "Red Sox"],
            "favorite_sports": ["basketball", "football", "baseball"]
        }
    ]

    for user in users:
        # Insert user
        user_id = await connection_pool.fetchval("""
            INSERT INTO users (
                id, email, username, full_name, is_active, favorite_teams, favorite_sports,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), $1, $2, $3, $4, $5, $6, NOW(), NOW()
            )
            ON CONFLICT (email) DO UPDATE SET
                username = EXCLUDED.username,
                full_name = EXCLUDED.full_name,
                is_active = EXCLUDED.is_active,
                favorite_teams = EXCLUDED.favorite_teams,
                favorite_sports = EXCLUDED.favorite_sports,
                updated_at = NOW()
            RETURNING id
        """,
            user["email"],
            user["username"],
            user["full_name"],
            user["is_active"],
            json.dumps(user["favorite_teams"]),
            json.dumps(user["favorite_sports"])
        )

    logger.info(f"Seeded {len(users)} users with preferences")


async def seed_trending_terms(connection_pool: ConnectionPool):
    """Seed sample trending terms"""

    trending_terms = [
        {
            "term": "LeBron James",
            "normalized_term": "lebron james",
            "term_type": "player",
            "count_1h": 150,
            "count_6h": 800,
            "count_24h": 2500,
            "burst_ratio": 0.85,
            "trend_score": 0.92,
            "is_trending": True,
            "sports_context": {"sport": "NBA", "teams": ["Lakers"]}
        },
        {
            "term": "NFL Draft",
            "normalized_term": "nfl draft",
            "term_type": "event",
            "count_1h": 200,
            "count_6h": 1200,
            "count_24h": 4000,
            "burst_ratio": 0.92,
            "trend_score": 0.95,
            "is_trending": True,
            "sports_context": {"sport": "NFL"}
        },
        {
            "term": "World Series",
            "normalized_term": "world series",
            "term_type": "event",
            "count_1h": 180,
            "count_6h": 900,
            "count_24h": 3200,
            "burst_ratio": 0.78,
            "trend_score": 0.88,
            "is_trending": True,
            "sports_context": {"sport": "MLB"}
        },
        {
            "term": "trade deadline",
            "normalized_term": "trade deadline",
            "term_type": "event",
            "count_1h": 120,
            "count_6h": 600,
            "count_24h": 1800,
            "burst_ratio": 0.65,
            "trend_score": 0.75,
            "is_trending": False,
            "sports_context": {"leagues": ["NBA", "NFL", "MLB"]}
        }
    ]

    for term in trending_terms:
        await connection_pool.execute("""
            INSERT INTO trending_terms (
                id, term, normalized_term, term_type, count_1h, count_6h, count_24h,
                burst_ratio, trend_score, is_trending, sports_context,
                created_at, updated_at, last_seen
            ) VALUES (
                gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), NOW(), NOW()
            )
            ON CONFLICT (normalized_term) DO UPDATE SET
                term = EXCLUDED.term,
                term_type = EXCLUDED.term_type,
                count_1h = EXCLUDED.count_1h,
                count_6h = EXCLUDED.count_6h,
                count_24h = EXCLUDED.count_24h,
                burst_ratio = EXCLUDED.burst_ratio,
                trend_score = EXCLUDED.trend_score,
                is_trending = EXCLUDED.is_trending,
                sports_context = EXCLUDED.sports_context,
                updated_at = NOW(),
                last_seen = NOW()
        """,
            term["term"],
            term["normalized_term"],
            term["term_type"],
            term["count_1h"],
            term["count_6h"],
            term["count_24h"],
            term["burst_ratio"],
            term["trend_score"],
            term["is_trending"],
            json.dumps(term["sports_context"])
        )

    logger.info(f"Seeded {len(trending_terms)} trending terms")


async def seed_sports(connection_pool: ConnectionPool) -> dict[str, str]:
    """Seed sports data"""

    sports = [
        {
            "name": "Basketball",
            "slug": "basketball",
            "description": "Professional and college basketball",
            "is_active": True
        },
        {
            "name": "Football",
            "slug": "football",
            "description": "NFL and college football",
            "is_active": True
        },
        {
            "name": "Baseball",
            "slug": "baseball",
            "description": "MLB and minor league baseball",
            "is_active": True
        },
        {
            "name": "Hockey",
            "slug": "hockey",
            "description": "NHL and international hockey",
            "is_active": True
        },
        {
            "name": "Soccer",
            "slug": "soccer",
            "description": "MLS and international soccer",
            "is_active": True
        }
    ]

    sport_ids = {}

    for sport in sports:
        sport_id = await connection_pool.fetchval(
            """
            INSERT INTO sports (name, slug, description, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, NOW(), NOW())
            ON CONFLICT (slug) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                is_active = EXCLUDED.is_active,
                updated_at = NOW()
            RETURNING id
            """,
            sport["name"],
            sport["slug"],
            sport["description"],
            sport["is_active"]
        )
        sport_ids[sport["slug"]] = sport_id

    logger.info(f"Seeded {len(sports)} sports")
    return sport_ids


async def seed_teams(connection_pool: ConnectionPool, sport_ids: dict[str, str]) -> None:
    """Seed teams data"""

    teams = [
        # NBA Teams
        {"name": "Los Angeles Lakers", "slug": "lakers", "display_name": "Los Angeles Lakers", "sport": "basketball", "city": "Los Angeles", "state": "CA", "country": "USA", "league": "NBA"},
        {"name": "Boston Celtics", "slug": "celtics", "display_name": "Boston Celtics", "sport": "basketball", "city": "Boston", "state": "MA", "country": "USA", "league": "NBA"},
        {"name": "Golden State Warriors", "slug": "warriors", "display_name": "Golden State Warriors", "sport": "basketball", "city": "San Francisco", "state": "CA", "country": "USA", "league": "NBA"},
        {"name": "Miami Heat", "slug": "heat", "display_name": "Miami Heat", "sport": "basketball", "city": "Miami", "state": "FL", "country": "USA", "league": "NBA"},

        # NFL Teams
        {"name": "Kansas City Chiefs", "slug": "chiefs", "display_name": "Kansas City Chiefs", "sport": "football", "city": "Kansas City", "state": "MO", "country": "USA", "league": "NFL"},
        {"name": "Buffalo Bills", "slug": "bills", "display_name": "Buffalo Bills", "sport": "football", "city": "Buffalo", "state": "NY", "country": "USA", "league": "NFL"},
        {"name": "San Francisco 49ers", "slug": "49ers", "display_name": "San Francisco 49ers", "sport": "football", "city": "San Francisco", "state": "CA", "country": "USA", "league": "NFL"},
        {"name": "Dallas Cowboys", "slug": "cowboys", "display_name": "Dallas Cowboys", "sport": "football", "city": "Dallas", "state": "TX", "country": "USA", "league": "NFL"},

        # MLB Teams
        {"name": "Los Angeles Dodgers", "slug": "dodgers", "display_name": "Los Angeles Dodgers", "sport": "baseball", "city": "Los Angeles", "state": "CA", "country": "USA", "league": "MLB"},
        {"name": "New York Yankees", "slug": "yankees", "display_name": "New York Yankees", "sport": "baseball", "city": "New York", "state": "NY", "country": "USA", "league": "MLB"},
        {"name": "Boston Red Sox", "slug": "red-sox", "display_name": "Boston Red Sox", "sport": "baseball", "city": "Boston", "state": "MA", "country": "USA", "league": "MLB"},
        {"name": "Atlanta Braves", "slug": "braves", "display_name": "Atlanta Braves", "sport": "baseball", "city": "Atlanta", "state": "GA", "country": "USA", "league": "MLB"},

        # NHL Teams
        {"name": "Tampa Bay Lightning", "slug": "lightning", "display_name": "Tampa Bay Lightning", "sport": "hockey", "city": "Tampa Bay", "state": "FL", "country": "USA", "league": "NHL"},
        {"name": "Colorado Avalanche", "slug": "avalanche", "display_name": "Colorado Avalanche", "sport": "hockey", "city": "Denver", "state": "CO", "country": "USA", "league": "NHL"},
        {"name": "Vegas Golden Knights", "slug": "golden-knights", "display_name": "Vegas Golden Knights", "sport": "hockey", "city": "Las Vegas", "state": "NV", "country": "USA", "league": "NHL"},
        {"name": "Boston Bruins", "slug": "bruins", "display_name": "Boston Bruins", "sport": "hockey", "city": "Boston", "state": "MA", "country": "USA", "league": "NHL"},

        # MLS Teams
        {"name": "LA Galaxy", "slug": "galaxy", "display_name": "LA Galaxy", "sport": "soccer", "city": "Los Angeles", "state": "CA", "country": "USA", "league": "MLS"},
        {"name": "Atlanta United FC", "slug": "atlanta-united", "display_name": "Atlanta United FC", "sport": "soccer", "city": "Atlanta", "state": "GA", "country": "USA", "league": "MLS"},
        {"name": "Seattle Sounders FC", "slug": "sounders", "display_name": "Seattle Sounders FC", "sport": "soccer", "city": "Seattle", "state": "WA", "country": "USA", "league": "MLS"},
        {"name": "New York City FC", "slug": "nycfc", "display_name": "New York City FC", "sport": "soccer", "city": "New York", "state": "NY", "country": "USA", "league": "MLS"}
    ]

    for team in teams:
        sport_id = sport_ids.get(team["sport"])
        if not sport_id:
            logger.warning(f"Sport '{team['sport']}' not found for team '{team['name']}'")
            continue

        await connection_pool.execute(
            """
            INSERT INTO teams (sport_id, name, slug, display_name, city, state, country, league, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW())
            ON CONFLICT (sport_id, slug) DO UPDATE SET
                name = EXCLUDED.name,
                display_name = EXCLUDED.display_name,
                city = EXCLUDED.city,
                state = EXCLUDED.state,
                country = EXCLUDED.country,
                league = EXCLUDED.league,
                is_active = EXCLUDED.is_active,
                updated_at = NOW()
            """,
            sport_id,
            team["name"],
            team["slug"],
            team["display_name"],
            team["city"],
            team["state"],
            team["country"],
            team["league"],
            True
        )

    logger.info(f"Seeded {len(teams)} teams")


async def main():
    """Main seeding function"""

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("Starting database seeding...")

    # Load settings
    settings = Settings()

    # Initialize database connection
    # Fix database URL for asyncpg compatibility
    db_url = settings.database.url.replace("postgresql+asyncpg://", "postgresql://")
    connection_pool = ConnectionPool(db_url)
    await connection_pool.initialize()

    try:
        # Seed data
        source_ids = await seed_sources(connection_pool)
        await seed_sample_content(connection_pool, source_ids)
        await seed_users(connection_pool)
        await seed_trending_terms(connection_pool)

        # Seed questionnaire data
        sport_ids = await seed_sports(connection_pool)
        await seed_teams(connection_pool, sport_ids)

        logger.info("✅ Database seeding completed successfully!")

    except Exception as e:
        logger.error(f"❌ Database seeding failed: {e}")
        raise

    finally:
        await connection_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
