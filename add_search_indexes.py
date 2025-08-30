#!/usr/bin/env python3
"""
Script to add database indexes for optimized query performance.

This script adds indexes that support:
1. User preference queries with joins
2. Content search and filtering
3. Authentication and authorization lookups
4. Trending and analytics queries
"""

import asyncio
import logging

from sqlalchemy import text

from libs.common.database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Index definitions for query optimization
INDEXES = [
    # User preference indexes with explicit join support
    {
        "name": "idx_user_sport_preferences_user_sport",
        "table": "user_sport_preferences",
        "columns": "user_id, sport_id",
        "description": "Optimize user sport preference lookups and joins"
    },
    {
        "name": "idx_user_team_preferences_user_team",
        "table": "user_team_preferences",
        "columns": "user_id, team_id",
        "description": "Optimize user team preference lookups and joins"
    },
    {
        "name": "idx_teams_sport_active",
        "table": "teams",
        "columns": "sport_id, is_active",
        "description": "Optimize team queries by sport with activity filter"
    },
    {
        "name": "idx_sports_active_display",
        "table": "sports",
        "columns": "is_active, display_name",
        "description": "Optimize active sports queries with ordering"
    },

    # Content and search indexes
    {
        "name": "idx_content_items_source_published",
        "table": "content_items",
        "columns": "source_id, published_at DESC",
        "description": "Optimize content queries by source and recency"
    },
    {
        "name": "idx_content_items_quality_published",
        "table": "content_items",
        "columns": "quality_score DESC, published_at DESC",
        "description": "Optimize content queries by quality and recency"
    },
    {
        "name": "idx_sources_active_name",
        "table": "sources",
        "columns": "is_active, name",
        "description": "Optimize source lookups and joins"
    },

    # Authentication and user management indexes
    {
        "name": "idx_users_email_active",
        "table": "users",
        "columns": "email, is_active",
        "description": "Optimize user authentication lookups"
    },
    {
        "name": "idx_user_roles_user_role",
        "table": "user_roles",
        "columns": "user_id, role",
        "description": "Optimize role-based authorization checks"
    },

    # Trending and analytics indexes
    {
        "name": "idx_trending_searches_timestamp",
        "table": "trending_searches",
        "columns": "timestamp DESC",
        "description": "Optimize trending search analytics"
    },
    {
        "name": "idx_user_interactions_user_timestamp",
        "table": "user_interactions",
        "columns": "user_id, timestamp DESC",
        "description": "Optimize user activity tracking"
    }
]

async def create_index(db_session, index_config):
    """Create a single database index."""
    try:
        # Check if index already exists
        check_query = text("""
            SELECT COUNT(*) as count
            FROM pg_indexes
            WHERE indexname = :index_name
        """)

        result = db_session.execute(check_query, {"index_name": index_config["name"]})
        exists = result.fetchone().count > 0

        if exists:
            logger.info(f"Index {index_config['name']} already exists, skipping")
            return True

        # Create the index
        create_query = text(f"""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_config['name']}
            ON {index_config['table']} ({index_config['columns']})
        """)

        logger.info(f"Creating index: {index_config['name']} - {index_config['description']}")
        db_session.execute(create_query)
        db_session.commit()

        logger.info(f"Successfully created index: {index_config['name']}")
        return True

    except Exception as e:
        logger.error(f"Failed to create index {index_config['name']}: {e!s}")
        db_session.rollback()
        return False

async def main():
    """Create all database indexes for query optimization."""
    logger.info("Starting database index creation for query optimization")

    db_gen = get_db()
    db_session = next(db_gen)

    try:
        success_count = 0
        total_count = len(INDEXES)

        for index_config in INDEXES:
            success = await create_index(db_session, index_config)
            if success:
                success_count += 1

        logger.info(f"Index creation completed: {success_count}/{total_count} successful")

        if success_count == total_count:
            logger.info("All indexes created successfully! Database is optimized for explicit joins.")
        else:
            logger.warning("Some indexes failed to create. Check logs for details.")

    except Exception as e:
        logger.error(f"Unexpected error during index creation: {e!s}")
    finally:
        db_session.close()

if __name__ == "__main__":
    asyncio.run(main())
