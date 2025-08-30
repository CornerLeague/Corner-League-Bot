#!/usr/bin/env python3
"""
Seed the database with sports and teams data for the questionnaire.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

from libs.common.config import Settings
from libs.common.database import DatabaseManager
from libs.common.questionnaire_models import Sport, Team

logger = logging.getLogger(__name__)

# Sports data with teams
SPORTS_DATA = [
    {
        "name": "Basketball",
        "slug": "basketball",
        "has_teams": True,
        "description": "Professional basketball including NBA, WNBA, and college basketball",
        "display_order": 1,
        "teams": [
            # NBA Teams
            {"name": "Los Angeles Lakers", "slug": "lakers", "city": "Los Angeles", "abbreviation": "LAL", "league": "NBA", "conference": "Western", "division": "Pacific"},
            {"name": "Boston Celtics", "slug": "celtics", "city": "Boston", "abbreviation": "BOS", "league": "NBA", "conference": "Eastern", "division": "Atlantic"},
            {"name": "Golden State Warriors", "slug": "warriors", "city": "Golden State", "abbreviation": "GSW", "league": "NBA", "conference": "Western", "division": "Pacific"},
            {"name": "Miami Heat", "slug": "heat", "city": "Miami", "abbreviation": "MIA", "league": "NBA", "conference": "Eastern", "division": "Southeast"},
            {"name": "Chicago Bulls", "slug": "bulls", "city": "Chicago", "abbreviation": "CHI", "league": "NBA", "conference": "Eastern", "division": "Central"},
            {"name": "San Antonio Spurs", "slug": "spurs", "city": "San Antonio", "abbreviation": "SAS", "league": "NBA", "conference": "Western", "division": "Southwest"},
            {"name": "New York Knicks", "slug": "knicks", "city": "New York", "abbreviation": "NYK", "league": "NBA", "conference": "Eastern", "division": "Atlantic"},
            {"name": "Dallas Mavericks", "slug": "mavericks", "city": "Dallas", "abbreviation": "DAL", "league": "NBA", "conference": "Western", "division": "Southwest"},
        ]
    },
    {
        "name": "Football (American)",
        "slug": "football",
        "has_teams": True,
        "description": "American football including NFL and college football",
        "display_order": 2,
        "teams": [
            # NFL Teams
            {"name": "New England Patriots", "slug": "patriots", "city": "New England", "abbreviation": "NE", "league": "NFL", "conference": "AFC", "division": "East"},
            {"name": "Dallas Cowboys", "slug": "cowboys", "city": "Dallas", "abbreviation": "DAL", "league": "NFL", "conference": "NFC", "division": "East"},
            {"name": "Green Bay Packers", "slug": "packers", "city": "Green Bay", "abbreviation": "GB", "league": "NFL", "conference": "NFC", "division": "North"},
            {"name": "Pittsburgh Steelers", "slug": "steelers", "city": "Pittsburgh", "abbreviation": "PIT", "league": "NFL", "conference": "AFC", "division": "North"},
            {"name": "San Francisco 49ers", "slug": "49ers", "city": "San Francisco", "abbreviation": "SF", "league": "NFL", "conference": "NFC", "division": "West"},
            {"name": "Kansas City Chiefs", "slug": "chiefs", "city": "Kansas City", "abbreviation": "KC", "league": "NFL", "conference": "AFC", "division": "West"},
            {"name": "Buffalo Bills", "slug": "bills", "city": "Buffalo", "abbreviation": "BUF", "league": "NFL", "conference": "AFC", "division": "East"},
            {"name": "Tampa Bay Buccaneers", "slug": "buccaneers", "city": "Tampa Bay", "abbreviation": "TB", "league": "NFL", "conference": "NFC", "division": "South"},
        ]
    },
    {
        "name": "Baseball",
        "slug": "baseball",
        "has_teams": True,
        "description": "Major League Baseball and college baseball",
        "display_order": 3,
        "teams": [
            # MLB Teams
            {"name": "New York Yankees", "slug": "yankees", "city": "New York", "abbreviation": "NYY", "league": "MLB", "conference": "American League", "division": "East"},
            {"name": "Los Angeles Dodgers", "slug": "dodgers", "city": "Los Angeles", "abbreviation": "LAD", "league": "MLB", "conference": "National League", "division": "West"},
            {"name": "Boston Red Sox", "slug": "red-sox", "city": "Boston", "abbreviation": "BOS", "league": "MLB", "conference": "American League", "division": "East"},
            {"name": "San Francisco Giants", "slug": "giants", "city": "San Francisco", "abbreviation": "SF", "league": "MLB", "conference": "National League", "division": "West"},
            {"name": "Chicago Cubs", "slug": "cubs", "city": "Chicago", "abbreviation": "CHC", "league": "MLB", "conference": "National League", "division": "Central"},
            {"name": "Atlanta Braves", "slug": "braves", "city": "Atlanta", "abbreviation": "ATL", "league": "MLB", "conference": "National League", "division": "East"},
        ]
    },
    {
        "name": "Soccer/Football (International)",
        "slug": "soccer",
        "has_teams": True,
        "description": "Major League Soccer, Premier League, and international soccer",
        "display_order": 4,
        "teams": [
            # MLS Teams
            {"name": "LA Galaxy", "slug": "la-galaxy", "city": "Los Angeles", "abbreviation": "LAG", "league": "MLS", "conference": "Western"},
            {"name": "New York City FC", "slug": "nycfc", "city": "New York City", "abbreviation": "NYC", "league": "MLS", "conference": "Eastern"},
            {"name": "Seattle Sounders FC", "slug": "sounders", "city": "Seattle", "abbreviation": "SEA", "league": "MLS", "conference": "Western"},
            {"name": "Atlanta United FC", "slug": "atlanta-united", "city": "Atlanta", "abbreviation": "ATL", "league": "MLS", "conference": "Eastern"},
            # Premier League Teams
            {"name": "Manchester United", "slug": "man-united", "city": "Manchester", "abbreviation": "MUN", "league": "Premier League"},
            {"name": "Liverpool FC", "slug": "liverpool", "city": "Liverpool", "abbreviation": "LIV", "league": "Premier League"},
            {"name": "Arsenal FC", "slug": "arsenal", "city": "London", "abbreviation": "ARS", "league": "Premier League"},
        ]
    },
    {
        "name": "Hockey",
        "slug": "hockey",
        "has_teams": True,
        "description": "National Hockey League and international hockey",
        "display_order": 5,
        "teams": [
            # NHL Teams
            {"name": "Boston Bruins", "slug": "bruins", "city": "Boston", "abbreviation": "BOS", "league": "NHL", "conference": "Eastern", "division": "Atlantic"},
            {"name": "Toronto Maple Leafs", "slug": "maple-leafs", "city": "Toronto", "abbreviation": "TOR", "league": "NHL", "conference": "Eastern", "division": "Atlantic"},
            {"name": "Montreal Canadiens", "slug": "canadiens", "city": "Montreal", "abbreviation": "MTL", "league": "NHL", "conference": "Eastern", "division": "Atlantic"},
            {"name": "Chicago Blackhawks", "slug": "blackhawks", "city": "Chicago", "abbreviation": "CHI", "league": "NHL", "conference": "Western", "division": "Central"},
            {"name": "Pittsburgh Penguins", "slug": "penguins", "city": "Pittsburgh", "abbreviation": "PIT", "league": "NHL", "conference": "Eastern", "division": "Metropolitan"},
        ]
    },
    {
        "name": "Tennis",
        "slug": "tennis",
        "has_teams": False,
        "description": "Professional tennis including ATP, WTA, and Grand Slams",
        "display_order": 6,
        "teams": []
    },
    {
        "name": "Golf",
        "slug": "golf",
        "has_teams": False,
        "description": "Professional golf including PGA Tour, European Tour, and majors",
        "display_order": 7,
        "teams": []
    },
    {
        "name": "F1",
        "slug": "f1",
        "has_teams": True,
        "description": "Formula 1 racing and motorsports",
        "display_order": 8,
        "teams": [
            # F1 Teams
            {"name": "Mercedes-AMG Petronas", "slug": "mercedes", "city": "Brackley", "abbreviation": "MER", "league": "Formula 1"},
            {"name": "Red Bull Racing", "slug": "red-bull", "city": "Milton Keynes", "abbreviation": "RBR", "league": "Formula 1"},
            {"name": "Scuderia Ferrari", "slug": "ferrari", "city": "Maranello", "abbreviation": "FER", "league": "Formula 1"},
            {"name": "McLaren F1 Team", "slug": "mclaren", "city": "Woking", "abbreviation": "MCL", "league": "Formula 1"},
        ]
    },
    {
        "name": "NASCAR",
        "slug": "nascar",
        "has_teams": True,
        "description": "NASCAR Cup Series and other stock car racing",
        "display_order": 9,
        "teams": [
            # NASCAR Teams
            {"name": "Hendrick Motorsports", "slug": "hendrick", "city": "Charlotte", "abbreviation": "HMS", "league": "NASCAR Cup Series"},
            {"name": "Joe Gibbs Racing", "slug": "jgr", "city": "Huntersville", "abbreviation": "JGR", "league": "NASCAR Cup Series"},
            {"name": "Team Penske", "slug": "penske", "city": "Mooresville", "abbreviation": "PEN", "league": "NASCAR Cup Series"},
            {"name": "Stewart-Haas Racing", "slug": "shr", "city": "Kannapolis", "abbreviation": "SHR", "league": "NASCAR Cup Series"},
        ]
    },
    {
        "name": "UFC",
        "slug": "ufc",
        "has_teams": False,
        "description": "Ultimate Fighting Championship and mixed martial arts",
        "display_order": 10,
        "teams": []
    },
    {
        "name": "Boxing",
        "slug": "boxing",
        "has_teams": False,
        "description": "Professional boxing across all weight classes",
        "display_order": 11,
        "teams": []
    },
    {
        "name": "Esports",
        "slug": "esports",
        "has_teams": True,
        "description": "Competitive gaming including League of Legends, CS:GO, and more",
        "display_order": 12,
        "teams": [
            # Esports Teams
            {"name": "Team SoloMid", "slug": "tsm", "city": "Los Angeles", "abbreviation": "TSM", "league": "LCS"},
            {"name": "Cloud9", "slug": "cloud9", "city": "Los Angeles", "abbreviation": "C9", "league": "LCS"},
            {"name": "FaZe Clan", "slug": "faze", "city": "Los Angeles", "abbreviation": "FAZE", "league": "Multiple"},
            {"name": "Team Liquid", "slug": "liquid", "city": "Los Angeles", "abbreviation": "TL", "league": "Multiple"},
        ]
    },
    {
        "name": "Olympics",
        "slug": "olympics",
        "has_teams": False,
        "description": "Summer and Winter Olympic Games coverage",
        "display_order": 13,
        "teams": []
    }
]


async def seed_sports_data():
    """Seed the database with sports and teams data."""
    settings = Settings()
    db_manager = DatabaseManager(settings.database.url)
    
    try:
        logger.info("Starting sports data seeding...")
        
        async with db_manager.transaction() as session:
            # Clear existing data
            logger.info("Clearing existing sports and teams data...")
            from sqlalchemy import text
            await session.execute(text("DELETE FROM user_team_preferences"))
            await session.execute(text("DELETE FROM user_sport_preferences"))
            await session.execute(text("DELETE FROM teams"))
            await session.execute(text("DELETE FROM sports"))
            await session.commit()
            
            # Insert sports
            logger.info("Inserting sports data...")
            for sport_data in SPORTS_DATA:
                sport = Sport(
                    name=sport_data["name"],
                    display_name=sport_data["name"],
                    description=sport_data.get("description"),
                    is_active=True
                )
                session.add(sport)
                await session.flush()  # Get the sport ID
                
                # Insert teams for this sport
                if sport_data["has_teams"] and "teams" in sport_data:
                    logger.info(f"Inserting teams for {sport_data['name']}...")
                    for team_data in sport_data["teams"]:
                        team = Team(
                            sport_id=sport.id,
                            name=team_data["name"],
                            display_name=team_data["name"],
                            city=team_data.get("city"),
                            league=team_data.get("league"),
                            is_active=True
                        )
                        session.add(team)
            
            await session.commit()
            logger.info("Sports and teams data seeded successfully!")
            
    except Exception as e:
        logger.error(f"Error seeding sports data: {e}")
        raise
    finally:
        await db_manager.close()


if __name__ == "__main__":
    import uuid
    from uuid import uuid4
    
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_sports_data())