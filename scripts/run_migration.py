#!/usr/bin/env python3
"""
Database migration script for questionnaire tables.
"""

import asyncio
import logging
from libs.common.config import Settings
from libs.common.database import DatabaseManager
from libs.common.questionnaire_models import Sport, Team, UserSportPreference, UserTeamPreference, QuestionnaireResponse, UserQuestionnaireStatus

logger = logging.getLogger(__name__)

async def run_migration():
    """Run the database migration to create questionnaire tables."""
    
    try:
        print("Running questionnaire tables migration...")
        
        # Initialize settings
        settings = Settings()
        print(f"Database URL: {settings.database.url}")
        
        # Create database manager
        db_manager = DatabaseManager(settings.database.url)
        
        print("Creating questionnaire tables...")
        
        # Create all tables defined in the questionnaire models
        await db_manager.create_tables()
        
        print("✅ Questionnaire tables created successfully!")
        
        # Close the database connection
        await db_manager.close()
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_migration())