#!/usr/bin/env python3
"""
Database seeding script for Sports Media Platform.
Seeds the database with initial data for development and testing.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from libs.common.config import Settings
from libs.common.database import ConnectionPool

logger = logging.getLogger(__name__)


async def seed_sources(connection_pool: ConnectionPool) -> List[str]:
    """Seed initial sports media sources"""
    
    sources = [
        # Major Sports Publishers
        {
            'domain': 'espn.com',
            'name': 'ESPN',
            'is_active': True,
            'priority': 1,
            'source_type': 'major_publisher',
            'rss_feeds': [
                'https://www.espn.com/espn/rss/news',
                'https://www.espn.com/espn/rss/nba/news',
                'https://www.espn.com/espn/rss/nfl/news',
                'https://www.espn.com/espn/rss/mlb/news'
            ]
        },
        {
            'domain': 'si.com',
            'name': 'Sports Illustrated',
            'is_active': True,
            'priority': 1,
            'source_type': 'major_publisher',
            'rss_feeds': [
                'https://www.si.com/rss/si_topstories.rss'
            ]
        },
        {
            'domain': 'theathletic.com',
            'name': 'The Athletic',
            'is_active': True,
            'priority': 1,
            'source_type': 'major_publisher',
            'rss_feeds': []
        },
        {
            'domain': 'cbssports.com',
            'name': 'CBS Sports',
            'is_active': True,
            'priority': 1,
            'source_type': 'major_publisher',
            'rss_feeds': [
                'https://www.cbssports.com/rss/headlines'
            ]
        },
        {
            'domain': 'foxsports.com',
            'name': 'Fox Sports',
            'is_active': True,
            'priority': 1,
            'source_type': 'major_publisher',
            'rss_feeds': []
        },
        
        # Team Official Sites
        {
            'domain': 'nba.com',
            'name': 'NBA Official',
            'is_active': True,
            'priority': 2,
            'source_type': 'league_official',
            'rss_feeds': [
                'https://www.nba.com/news/rss.xml'
            ]
        },
        {
            'domain': 'nfl.com',
            'name': 'NFL Official',
            'is_active': True,
            'priority': 2,
            'source_type': 'league_official',
            'rss_feeds': [
                'https://www.nfl.com/news/rss.xml'
            ]
        },
        {
            'domain': 'mlb.com',
            'name': 'MLB Official',
            'is_active': True,
            'priority': 2,
            'source_type': 'league_official',
            'rss_feeds': [
                'https://www.mlb.com/news/rss.xml'
            ]
        },
        
        # Sports Blogs
        {
            'domain': 'sbnation.com',
            'name': 'SB Nation',
            'is_active': True,
            'priority': 3,
            'source_type': 'sports_blog',
            'rss_feeds': [
                'https://www.sbnation.com/rss/index.xml'
            ]
        },
        {
            'domain': 'bleacherreport.com',
            'name': 'Bleacher Report',
            'is_active': True,
            'priority': 3,
            'source_type': 'sports_blog',
            'rss_feeds': [
                'https://bleacherreport.com/articles.rss'
            ]
        },
        
        # Regional Sports Media
        {
            'domain': 'latimes.com',
            'name': 'LA Times Sports',
            'is_active': True,
            'priority': 3,
            'source_type': 'regional_media',
            'rss_feeds': []
        },
        {
            'domain': 'boston.com',
            'name': 'Boston.com Sports',
            'is_active': True,
            'priority': 3,
            'source_type': 'regional_media',
            'rss_feeds': []
        }
    ]
    
    source_ids = []
    
    for source_data in sources:
        # Insert source
        source_id = await connection_pool.fetchval("""
            INSERT INTO sources (
                id, domain, name, is_active, priority, source_type,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), $1, $2, $3, $4, $5, NOW(), NOW()
            ) 
            ON CONFLICT (domain) DO UPDATE SET
                name = EXCLUDED.name,
                is_active = EXCLUDED.is_active,
                priority = EXCLUDED.priority,
                source_type = EXCLUDED.source_type,
                updated_at = NOW()
            RETURNING id
        """, 
            source_data['domain'],
            source_data['name'],
            source_data['is_active'],
            source_data['priority'],
            source_data['source_type']
        )
        
        source_ids.append(source_id)
        
        # Insert RSS feeds
        for rss_url in source_data['rss_feeds']:
            await connection_pool.execute("""
                INSERT INTO rss_feeds (
                    id, url, source_id, is_active, priority,
                    created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), $1, $2, true, 1, NOW(), NOW()
                )
                ON CONFLICT (url) DO NOTHING
            """, rss_url, source_id)
    
    logger.info(f"Seeded {len(sources)} sources with RSS feeds")
    return source_ids


async def seed_sample_content(connection_pool: ConnectionPool, source_ids: List[str]):
    """Seed sample content items for testing"""
    
    sample_articles = [
        {
            'title': 'Lakers Defeat Warriors in Overtime Thriller',
            'byline': 'ESPN Staff',
            'text': 'In a thrilling overtime battle at Crypto.com Arena, the Los Angeles Lakers defeated the Golden State Warriors 128-125. LeBron James led the Lakers with 35 points, 8 rebounds, and 12 assists in what many are calling one of the games of the season. The victory moves the Lakers to 25-15 on the season and strengthens their position in the Western Conference playoff race.',
            'summary': 'Lakers beat Warriors 128-125 in overtime with LeBron James scoring 35 points.',
            'canonical_url': 'https://espn.com/nba/story/lakers-warriors-overtime-thriller',
            'original_url': 'https://espn.com/nba/story/lakers-warriors-overtime-thriller',
            'published_at': datetime.utcnow() - timedelta(hours=2),
            'quality_score': 0.92,
            'sports_keywords': ['Lakers', 'Warriors', 'NBA', 'LeBron James', 'overtime'],
            'content_type': 'game_recap',
            'word_count': 156,
            'language': 'en'
        },
        {
            'title': 'NFL Draft Prospects: Top 10 Quarterbacks to Watch',
            'byline': 'Sports Illustrated',
            'text': 'As the NFL Draft approaches, quarterback prospects are generating significant buzz among scouts and analysts. Leading the pack is Caleb Williams from USC, whose combination of arm strength and mobility has impressed evaluators. Drake Maye from North Carolina and Jayden Daniels from LSU round out the top three in most draft boards. This quarterback class is considered one of the strongest in recent years.',
            'summary': 'Analysis of top NFL Draft quarterback prospects led by Caleb Williams, Drake Maye, and Jayden Daniels.',
            'canonical_url': 'https://si.com/nfl/draft-prospects-quarterbacks-2024',
            'original_url': 'https://si.com/nfl/draft-prospects-quarterbacks-2024',
            'published_at': datetime.utcnow() - timedelta(hours=6),
            'quality_score': 0.88,
            'sports_keywords': ['NFL', 'Draft', 'quarterbacks', 'Caleb Williams', 'Drake Maye'],
            'content_type': 'analysis',
            'word_count': 134,
            'language': 'en'
        },
        {
            'title': 'World Series Preview: Dodgers vs Yankees',
            'byline': 'CBS Sports',
            'text': 'The stage is set for a classic World Series matchup between the Los Angeles Dodgers and New York Yankees. Both teams finished with over 100 wins during the regular season and have looked dominant throughout the playoffs. The Dodgers boast the best offense in baseball, while the Yankees counter with exceptional pitching depth. Game 1 is scheduled for Friday night at Yankee Stadium.',
            'summary': 'World Series preview between the 100-win Dodgers and Yankees, starting Friday at Yankee Stadium.',
            'canonical_url': 'https://cbssports.com/mlb/world-series-preview-dodgers-yankees',
            'original_url': 'https://cbssports.com/mlb/world-series-preview-dodgers-yankees',
            'published_at': datetime.utcnow() - timedelta(hours=12),
            'quality_score': 0.85,
            'sports_keywords': ['MLB', 'World Series', 'Dodgers', 'Yankees', 'playoffs'],
            'content_type': 'preview',
            'word_count': 118,
            'language': 'en'
        },
        {
            'title': 'Trade Deadline Recap: Major Moves Across the League',
            'byline': 'The Athletic',
            'text': 'The NBA trade deadline delivered several blockbuster moves that could reshape the playoff picture. The Phoenix Suns acquired Bradley Beal from Washington in exchange for multiple first-round picks and young players. Meanwhile, the Miami Heat bolster their frontcourt by trading for Kristaps Porzingis. These moves signal an arms race among contending teams as the playoffs approach.',
            'summary': 'NBA trade deadline recap featuring Bradley Beal to Phoenix and Kristaps Porzingis to Miami.',
            'canonical_url': 'https://theathletic.com/nba/trade-deadline-recap-major-moves',
            'original_url': 'https://theathletic.com/nba/trade-deadline-recap-major-moves',
            'published_at': datetime.utcnow() - timedelta(days=1),
            'quality_score': 0.90,
            'sports_keywords': ['NBA', 'trade deadline', 'Bradley Beal', 'Kristaps Porzingis', 'playoffs'],
            'content_type': 'news',
            'word_count': 142,
            'language': 'en'
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
            article['title'],
            article['byline'],
            article['text'],
            article['summary'],
            article['canonical_url'],
            article['original_url'],
            article['published_at'],
            article['quality_score'],
            article['sports_keywords'],
            article['content_type'],
            source_id,
            article['word_count'],
            article['language'],
            f"hash_{i}"  # Simple hash for demo
        )
    
    logger.info(f"Seeded {len(sample_articles)} sample content items")


async def seed_users(connection_pool: ConnectionPool):
    """Seed sample users for testing"""
    
    users = [
        {
            'email': 'admin@sportsmedia.com',
            'username': 'admin',
            'full_name': 'Admin User',
            'role': 'admin',
            'is_active': True,
            'preferences': {
                'favorite_teams': ['Lakers', 'Dodgers', 'Rams'],
                'favorite_sports': ['basketball', 'baseball', 'football'],
                'content_types': ['news', 'analysis', 'game_recap']
            }
        },
        {
            'email': 'editor@sportsmedia.com',
            'username': 'editor',
            'full_name': 'Editor User',
            'role': 'editor',
            'is_active': True,
            'preferences': {
                'favorite_teams': ['Warriors', 'Giants', '49ers'],
                'favorite_sports': ['basketball', 'baseball', 'football'],
                'content_types': ['news', 'analysis']
            }
        },
        {
            'email': 'user@sportsmedia.com',
            'username': 'testuser',
            'full_name': 'Test User',
            'role': 'user',
            'is_active': True,
            'preferences': {
                'favorite_teams': ['Celtics', 'Patriots', 'Red Sox'],
                'favorite_sports': ['basketball', 'football', 'baseball'],
                'content_types': ['news', 'game_recap']
            }
        }
    ]
    
    for user in users:
        # Insert user
        user_id = await connection_pool.fetchval("""
            INSERT INTO users (
                id, email, username, full_name, role, is_active,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), $1, $2, $3, $4, $5, NOW(), NOW()
            )
            ON CONFLICT (email) DO UPDATE SET
                username = EXCLUDED.username,
                full_name = EXCLUDED.full_name,
                role = EXCLUDED.role,
                is_active = EXCLUDED.is_active,
                updated_at = NOW()
            RETURNING id
        """,
            user['email'],
            user['username'],
            user['full_name'],
            user['role'],
            user['is_active']
        )
        
        # Insert user preferences
        await connection_pool.execute("""
            INSERT INTO user_preferences (
                id, user_id, favorite_teams, favorite_sports, content_types,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), $1, $2, $3, $4, NOW(), NOW()
            )
            ON CONFLICT (user_id) DO UPDATE SET
                favorite_teams = EXCLUDED.favorite_teams,
                favorite_sports = EXCLUDED.favorite_sports,
                content_types = EXCLUDED.content_types,
                updated_at = NOW()
        """,
            user_id,
            user['preferences']['favorite_teams'],
            user['preferences']['favorite_sports'],
            user['preferences']['content_types']
        )
    
    logger.info(f"Seeded {len(users)} users with preferences")


async def seed_trending_terms(connection_pool: ConnectionPool):
    """Seed sample trending terms"""
    
    trending_terms = [
        {
            'term': 'LeBron James',
            'category': 'player',
            'frequency_1h': 150,
            'frequency_6h': 800,
            'frequency_24h': 2500,
            'burst_score': 0.85,
            'sports_context': ['NBA', 'Lakers']
        },
        {
            'term': 'NFL Draft',
            'category': 'event',
            'frequency_1h': 200,
            'frequency_6h': 1200,
            'frequency_24h': 4000,
            'burst_score': 0.92,
            'sports_context': ['NFL']
        },
        {
            'term': 'World Series',
            'category': 'event',
            'frequency_1h': 180,
            'frequency_6h': 900,
            'frequency_24h': 3200,
            'burst_score': 0.78,
            'sports_context': ['MLB']
        },
        {
            'term': 'trade deadline',
            'category': 'event',
            'frequency_1h': 120,
            'frequency_6h': 600,
            'frequency_24h': 1800,
            'burst_score': 0.65,
            'sports_context': ['NBA', 'NFL', 'MLB']
        }
    ]
    
    for term in trending_terms:
        await connection_pool.execute("""
            INSERT INTO trending_terms (
                id, term, category, frequency_1h, frequency_6h, frequency_24h,
                burst_score, sports_context, created_at, updated_at
            ) VALUES (
                gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7, NOW(), NOW()
            )
            ON CONFLICT (term) DO UPDATE SET
                frequency_1h = EXCLUDED.frequency_1h,
                frequency_6h = EXCLUDED.frequency_6h,
                frequency_24h = EXCLUDED.frequency_24h,
                burst_score = EXCLUDED.burst_score,
                sports_context = EXCLUDED.sports_context,
                updated_at = NOW()
        """,
            term['term'],
            term['category'],
            term['frequency_1h'],
            term['frequency_6h'],
            term['frequency_24h'],
            term['burst_score'],
            term['sports_context']
        )
    
    logger.info(f"Seeded {len(trending_terms)} trending terms")


async def main():
    """Main seeding function"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting database seeding...")
    
    # Load settings
    settings = Settings()
    
    # Initialize database connection
    connection_pool = ConnectionPool(settings.database.url)
    await connection_pool.initialize()
    
    try:
        # Seed data
        source_ids = await seed_sources(connection_pool)
        await seed_sample_content(connection_pool, source_ids)
        await seed_users(connection_pool)
        await seed_trending_terms(connection_pool)
        
        logger.info("✅ Database seeding completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database seeding failed: {e}")
        raise
    
    finally:
        await connection_pool.close()


if __name__ == "__main__":
    asyncio.run(main())

