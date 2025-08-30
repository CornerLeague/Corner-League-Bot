#!/usr/bin/env python3
"""
Seed the database with comprehensive sports and teams data extracted from the provided documents.
This script populates the database with teams from Basketball, Football, Baseball, Hockey, and Soccer.
"""

import asyncio
import logging

from libs.common.config import Settings
from libs.common.database import DatabaseManager
from libs.common.questionnaire_models import Sport, Team

logger = logging.getLogger(__name__)

# Comprehensive sports data extracted from the provided documents
COMPREHENSIVE_SPORTS_DATA = [
    {
        "name": "Basketball",
        "display_name": "Basketball",
        "description": "Professional basketball including NBA, WNBA, NCAA, and EuroLeague",
        "teams": [
            # NBA Teams
            {"name": "Atlanta Hawks", "display_name": "Atlanta Hawks", "city": "Atlanta", "state": "Georgia", "country": "USA", "league": "NBA"},
            {"name": "Boston Celtics", "display_name": "Boston Celtics", "city": "Boston", "state": "Massachusetts", "country": "USA", "league": "NBA"},
            {"name": "Brooklyn Nets", "display_name": "Brooklyn Nets", "city": "Brooklyn", "state": "New York", "country": "USA", "league": "NBA"},
            {"name": "Charlotte Hornets", "display_name": "Charlotte Hornets", "city": "Charlotte", "state": "North Carolina", "country": "USA", "league": "NBA"},
            {"name": "Chicago Bulls", "display_name": "Chicago Bulls", "city": "Chicago", "state": "Illinois", "country": "USA", "league": "NBA"},
            {"name": "Cleveland Cavaliers", "display_name": "Cleveland Cavaliers", "city": "Cleveland", "state": "Ohio", "country": "USA", "league": "NBA"},
            {"name": "Dallas Mavericks", "display_name": "Dallas Mavericks", "city": "Dallas", "state": "Texas", "country": "USA", "league": "NBA"},
            {"name": "Denver Nuggets", "display_name": "Denver Nuggets", "city": "Denver", "state": "Colorado", "country": "USA", "league": "NBA"},
            {"name": "Detroit Pistons", "display_name": "Detroit Pistons", "city": "Detroit", "state": "Michigan", "country": "USA", "league": "NBA"},
            {"name": "Golden State Warriors", "display_name": "Golden State Warriors", "city": "San Francisco", "state": "California", "country": "USA", "league": "NBA"},
            {"name": "Houston Rockets", "display_name": "Houston Rockets", "city": "Houston", "state": "Texas", "country": "USA", "league": "NBA"},
            {"name": "Indiana Pacers", "display_name": "Indiana Pacers", "city": "Indianapolis", "state": "Indiana", "country": "USA", "league": "NBA"},
            {"name": "LA Clippers", "display_name": "LA Clippers", "city": "Los Angeles", "state": "California", "country": "USA", "league": "NBA"},
            {"name": "Los Angeles Lakers", "display_name": "Los Angeles Lakers", "city": "Los Angeles", "state": "California", "country": "USA", "league": "NBA"},
            {"name": "Memphis Grizzlies", "display_name": "Memphis Grizzlies", "city": "Memphis", "state": "Tennessee", "country": "USA", "league": "NBA"},
            {"name": "Miami Heat", "display_name": "Miami Heat", "city": "Miami", "state": "Florida", "country": "USA", "league": "NBA"},
            {"name": "Milwaukee Bucks", "display_name": "Milwaukee Bucks", "city": "Milwaukee", "state": "Wisconsin", "country": "USA", "league": "NBA"},
            {"name": "Minnesota Timberwolves", "display_name": "Minnesota Timberwolves", "city": "Minneapolis", "state": "Minnesota", "country": "USA", "league": "NBA"},
            {"name": "New Orleans Pelicans", "display_name": "New Orleans Pelicans", "city": "New Orleans", "state": "Louisiana", "country": "USA", "league": "NBA"},
            {"name": "New York Knicks", "display_name": "New York Knicks", "city": "New York", "state": "New York", "country": "USA", "league": "NBA"},
            {"name": "Oklahoma City Thunder", "display_name": "Oklahoma City Thunder", "city": "Oklahoma City", "state": "Oklahoma", "country": "USA", "league": "NBA"},
            {"name": "Orlando Magic", "display_name": "Orlando Magic", "city": "Orlando", "state": "Florida", "country": "USA", "league": "NBA"},
            {"name": "Philadelphia 76ers", "display_name": "Philadelphia 76ers", "city": "Philadelphia", "state": "Pennsylvania", "country": "USA", "league": "NBA"},
            {"name": "Phoenix Suns", "display_name": "Phoenix Suns", "city": "Phoenix", "state": "Arizona", "country": "USA", "league": "NBA"},
            {"name": "Portland Trail Blazers", "display_name": "Portland Trail Blazers", "city": "Portland", "state": "Oregon", "country": "USA", "league": "NBA"},
            {"name": "Sacramento Kings", "display_name": "Sacramento Kings", "city": "Sacramento", "state": "California", "country": "USA", "league": "NBA"},
            {"name": "San Antonio Spurs", "display_name": "San Antonio Spurs", "city": "San Antonio", "state": "Texas", "country": "USA", "league": "NBA"},
            {"name": "Toronto Raptors", "display_name": "Toronto Raptors", "city": "Toronto", "state": "Ontario", "country": "Canada", "league": "NBA"},
            {"name": "Utah Jazz", "display_name": "Utah Jazz", "city": "Salt Lake City", "state": "Utah", "country": "USA", "league": "NBA"},
            {"name": "Washington Wizards", "display_name": "Washington Wizards", "city": "Washington", "state": "D.C.", "country": "USA", "league": "NBA"},

            # WNBA Teams
            {"name": "Atlanta Dream", "display_name": "Atlanta Dream", "city": "Atlanta", "state": "Georgia", "country": "USA", "league": "WNBA"},
            {"name": "Chicago Sky", "display_name": "Chicago Sky", "city": "Chicago", "state": "Illinois", "country": "USA", "league": "WNBA"},
            {"name": "Connecticut Sun", "display_name": "Connecticut Sun", "city": "Uncasville", "state": "Connecticut", "country": "USA", "league": "WNBA"},
            {"name": "Dallas Wings", "display_name": "Dallas Wings", "city": "Dallas", "state": "Texas", "country": "USA", "league": "WNBA"},
            {"name": "Indiana Fever", "display_name": "Indiana Fever", "city": "Indianapolis", "state": "Indiana", "country": "USA", "league": "WNBA"},
            {"name": "Las Vegas Aces", "display_name": "Las Vegas Aces", "city": "Las Vegas", "state": "Nevada", "country": "USA", "league": "WNBA"},
            {"name": "Minnesota Lynx", "display_name": "Minnesota Lynx", "city": "Minneapolis", "state": "Minnesota", "country": "USA", "league": "WNBA"},
            {"name": "New York Liberty", "display_name": "New York Liberty", "city": "New York", "state": "New York", "country": "USA", "league": "WNBA"},
            {"name": "Phoenix Mercury", "display_name": "Phoenix Mercury", "city": "Phoenix", "state": "Arizona", "country": "USA", "league": "WNBA"},
            {"name": "Seattle Storm", "display_name": "Seattle Storm", "city": "Seattle", "state": "Washington", "country": "USA", "league": "WNBA"},
            {"name": "Washington Mystics", "display_name": "Washington Mystics", "city": "Washington", "state": "D.C.", "country": "USA", "league": "WNBA"},

            # EuroLeague Teams (2024-2025 Season)
            {"name": "Real Madrid", "display_name": "Real Madrid", "city": "Madrid", "country": "Spain", "league": "EuroLeague"},
            {"name": "FC Barcelona", "display_name": "FC Barcelona", "city": "Barcelona", "country": "Spain", "league": "EuroLeague"},
            {"name": "Panathinaikos AKTOR Athens", "display_name": "Panathinaikos AKTOR Athens", "city": "Athens", "country": "Greece", "league": "EuroLeague"},
            {"name": "Olympiacos Piraeus", "display_name": "Olympiacos Piraeus", "city": "Piraeus", "country": "Greece", "league": "EuroLeague"},
            {"name": "Fenerbahce Beko Istanbul", "display_name": "Fenerbahce Beko Istanbul", "city": "Istanbul", "country": "Turkey", "league": "EuroLeague"},
            {"name": "Anadolu Efes Istanbul", "display_name": "Anadolu Efes Istanbul", "city": "Istanbul", "country": "Turkey", "league": "EuroLeague"},
            {"name": "CSKA Moscow", "display_name": "CSKA Moscow", "city": "Moscow", "country": "Russia", "league": "EuroLeague"},
            {"name": "Zalgiris Kaunas", "display_name": "Zalgiris Kaunas", "city": "Kaunas", "country": "Lithuania", "league": "EuroLeague"},
        ]
    },
    {
        "name": "Football",
        "display_name": "American Football",
        "description": "American football including NFL and NCAA",
        "teams": [
            # NFL Teams
            {"name": "Arizona Cardinals", "display_name": "Arizona Cardinals", "city": "Glendale", "state": "Arizona", "country": "USA", "league": "NFL"},
            {"name": "Atlanta Falcons", "display_name": "Atlanta Falcons", "city": "Atlanta", "state": "Georgia", "country": "USA", "league": "NFL"},
            {"name": "Baltimore Ravens", "display_name": "Baltimore Ravens", "city": "Baltimore", "state": "Maryland", "country": "USA", "league": "NFL"},
            {"name": "Buffalo Bills", "display_name": "Buffalo Bills", "city": "Buffalo", "state": "New York", "country": "USA", "league": "NFL"},
            {"name": "Carolina Panthers", "display_name": "Carolina Panthers", "city": "Charlotte", "state": "North Carolina", "country": "USA", "league": "NFL"},
            {"name": "Chicago Bears", "display_name": "Chicago Bears", "city": "Chicago", "state": "Illinois", "country": "USA", "league": "NFL"},
            {"name": "Cincinnati Bengals", "display_name": "Cincinnati Bengals", "city": "Cincinnati", "state": "Ohio", "country": "USA", "league": "NFL"},
            {"name": "Cleveland Browns", "display_name": "Cleveland Browns", "city": "Cleveland", "state": "Ohio", "country": "USA", "league": "NFL"},
            {"name": "Dallas Cowboys", "display_name": "Dallas Cowboys", "city": "Dallas", "state": "Texas", "country": "USA", "league": "NFL"},
            {"name": "Denver Broncos", "display_name": "Denver Broncos", "city": "Denver", "state": "Colorado", "country": "USA", "league": "NFL"},
            {"name": "Detroit Lions", "display_name": "Detroit Lions", "city": "Detroit", "state": "Michigan", "country": "USA", "league": "NFL"},
            {"name": "Green Bay Packers", "display_name": "Green Bay Packers", "city": "Green Bay", "state": "Wisconsin", "country": "USA", "league": "NFL"},
            {"name": "Houston Texans", "display_name": "Houston Texans", "city": "Houston", "state": "Texas", "country": "USA", "league": "NFL"},
            {"name": "Indianapolis Colts", "display_name": "Indianapolis Colts", "city": "Indianapolis", "state": "Indiana", "country": "USA", "league": "NFL"},
            {"name": "Jacksonville Jaguars", "display_name": "Jacksonville Jaguars", "city": "Jacksonville", "state": "Florida", "country": "USA", "league": "NFL"},
            {"name": "Kansas City Chiefs", "display_name": "Kansas City Chiefs", "city": "Kansas City", "state": "Missouri", "country": "USA", "league": "NFL"},
            {"name": "Las Vegas Raiders", "display_name": "Las Vegas Raiders", "city": "Las Vegas", "state": "Nevada", "country": "USA", "league": "NFL"},
            {"name": "Los Angeles Chargers", "display_name": "Los Angeles Chargers", "city": "Los Angeles", "state": "California", "country": "USA", "league": "NFL"},
            {"name": "Los Angeles Rams", "display_name": "Los Angeles Rams", "city": "Los Angeles", "state": "California", "country": "USA", "league": "NFL"},
            {"name": "Miami Dolphins", "display_name": "Miami Dolphins", "city": "Miami", "state": "Florida", "country": "USA", "league": "NFL"},
            {"name": "Minnesota Vikings", "display_name": "Minnesota Vikings", "city": "Minneapolis", "state": "Minnesota", "country": "USA", "league": "NFL"},
            {"name": "New England Patriots", "display_name": "New England Patriots", "city": "Foxborough", "state": "Massachusetts", "country": "USA", "league": "NFL"},
            {"name": "New Orleans Saints", "display_name": "New Orleans Saints", "city": "New Orleans", "state": "Louisiana", "country": "USA", "league": "NFL"},
            {"name": "New York Giants", "display_name": "New York Giants", "city": "East Rutherford", "state": "New Jersey", "country": "USA", "league": "NFL"},
            {"name": "New York Jets", "display_name": "New York Jets", "city": "East Rutherford", "state": "New Jersey", "country": "USA", "league": "NFL"},
            {"name": "Philadelphia Eagles", "display_name": "Philadelphia Eagles", "city": "Philadelphia", "state": "Pennsylvania", "country": "USA", "league": "NFL"},
            {"name": "Pittsburgh Steelers", "display_name": "Pittsburgh Steelers", "city": "Pittsburgh", "state": "Pennsylvania", "country": "USA", "league": "NFL"},
            {"name": "San Francisco 49ers", "display_name": "San Francisco 49ers", "city": "San Francisco", "state": "California", "country": "USA", "league": "NFL"},
            {"name": "Seattle Seahawks", "display_name": "Seattle Seahawks", "city": "Seattle", "state": "Washington", "country": "USA", "league": "NFL"},
            {"name": "Tampa Bay Buccaneers", "display_name": "Tampa Bay Buccaneers", "city": "Tampa", "state": "Florida", "country": "USA", "league": "NFL"},
            {"name": "Tennessee Titans", "display_name": "Tennessee Titans", "city": "Nashville", "state": "Tennessee", "country": "USA", "league": "NFL"},
            {"name": "Washington Commanders", "display_name": "Washington Commanders", "city": "Washington", "state": "D.C.", "country": "USA", "league": "NFL"},
        ]
    },
    {
        "name": "Baseball",
        "display_name": "Baseball",
        "description": "Major League Baseball and NCAA baseball",
        "teams": [
            # MLB Teams - American League
            {"name": "Baltimore Orioles", "display_name": "Baltimore Orioles", "city": "Baltimore", "state": "Maryland", "country": "USA", "league": "MLB"},
            {"name": "Boston Red Sox", "display_name": "Boston Red Sox", "city": "Boston", "state": "Massachusetts", "country": "USA", "league": "MLB"},
            {"name": "New York Yankees", "display_name": "New York Yankees", "city": "New York", "state": "New York", "country": "USA", "league": "MLB"},
            {"name": "Tampa Bay Rays", "display_name": "Tampa Bay Rays", "city": "St. Petersburg", "state": "Florida", "country": "USA", "league": "MLB"},
            {"name": "Toronto Blue Jays", "display_name": "Toronto Blue Jays", "city": "Toronto", "state": "Ontario", "country": "Canada", "league": "MLB"},
            {"name": "Chicago White Sox", "display_name": "Chicago White Sox", "city": "Chicago", "state": "Illinois", "country": "USA", "league": "MLB"},
            {"name": "Cleveland Guardians", "display_name": "Cleveland Guardians", "city": "Cleveland", "state": "Ohio", "country": "USA", "league": "MLB"},
            {"name": "Detroit Tigers", "display_name": "Detroit Tigers", "city": "Detroit", "state": "Michigan", "country": "USA", "league": "MLB"},
            {"name": "Kansas City Royals", "display_name": "Kansas City Royals", "city": "Kansas City", "state": "Missouri", "country": "USA", "league": "MLB"},
            {"name": "Minnesota Twins", "display_name": "Minnesota Twins", "city": "Minneapolis", "state": "Minnesota", "country": "USA", "league": "MLB"},
            {"name": "Houston Astros", "display_name": "Houston Astros", "city": "Houston", "state": "Texas", "country": "USA", "league": "MLB"},
            {"name": "Los Angeles Angels", "display_name": "Los Angeles Angels", "city": "Anaheim", "state": "California", "country": "USA", "league": "MLB"},
            {"name": "Oakland Athletics", "display_name": "Oakland Athletics", "city": "Oakland", "state": "California", "country": "USA", "league": "MLB"},
            {"name": "Seattle Mariners", "display_name": "Seattle Mariners", "city": "Seattle", "state": "Washington", "country": "USA", "league": "MLB"},
            {"name": "Texas Rangers", "display_name": "Texas Rangers", "city": "Arlington", "state": "Texas", "country": "USA", "league": "MLB"},

            # MLB Teams - National League
            {"name": "Atlanta Braves", "display_name": "Atlanta Braves", "city": "Atlanta", "state": "Georgia", "country": "USA", "league": "MLB"},
            {"name": "Miami Marlins", "display_name": "Miami Marlins", "city": "Miami", "state": "Florida", "country": "USA", "league": "MLB"},
            {"name": "New York Mets", "display_name": "New York Mets", "city": "New York", "state": "New York", "country": "USA", "league": "MLB"},
            {"name": "Philadelphia Phillies", "display_name": "Philadelphia Phillies", "city": "Philadelphia", "state": "Pennsylvania", "country": "USA", "league": "MLB"},
            {"name": "Washington Nationals", "display_name": "Washington Nationals", "city": "Washington", "state": "D.C.", "country": "USA", "league": "MLB"},
            {"name": "Chicago Cubs", "display_name": "Chicago Cubs", "city": "Chicago", "state": "Illinois", "country": "USA", "league": "MLB"},
            {"name": "Cincinnati Reds", "display_name": "Cincinnati Reds", "city": "Cincinnati", "state": "Ohio", "country": "USA", "league": "MLB"},
            {"name": "Milwaukee Brewers", "display_name": "Milwaukee Brewers", "city": "Milwaukee", "state": "Wisconsin", "country": "USA", "league": "MLB"},
            {"name": "Pittsburgh Pirates", "display_name": "Pittsburgh Pirates", "city": "Pittsburgh", "state": "Pennsylvania", "country": "USA", "league": "MLB"},
            {"name": "St. Louis Cardinals", "display_name": "St. Louis Cardinals", "city": "St. Louis", "state": "Missouri", "country": "USA", "league": "MLB"},
            {"name": "Arizona Diamondbacks", "display_name": "Arizona Diamondbacks", "city": "Phoenix", "state": "Arizona", "country": "USA", "league": "MLB"},
            {"name": "Colorado Rockies", "display_name": "Colorado Rockies", "city": "Denver", "state": "Colorado", "country": "USA", "league": "MLB"},
            {"name": "Los Angeles Dodgers", "display_name": "Los Angeles Dodgers", "city": "Los Angeles", "state": "California", "country": "USA", "league": "MLB"},
            {"name": "San Diego Padres", "display_name": "San Diego Padres", "city": "San Diego", "state": "California", "country": "USA", "league": "MLB"},
            {"name": "San Francisco Giants", "display_name": "San Francisco Giants", "city": "San Francisco", "state": "California", "country": "USA", "league": "MLB"},
        ]
    },
    {
        "name": "Hockey",
        "display_name": "Hockey",
        "description": "National Hockey League and international hockey",
        "teams": [
            # NHL Teams - Eastern Conference Atlantic Division
            {"name": "Boston Bruins", "display_name": "Boston Bruins", "city": "Boston", "state": "Massachusetts", "country": "USA", "league": "NHL"},
            {"name": "Buffalo Sabres", "display_name": "Buffalo Sabres", "city": "Buffalo", "state": "New York", "country": "USA", "league": "NHL"},
            {"name": "Detroit Red Wings", "display_name": "Detroit Red Wings", "city": "Detroit", "state": "Michigan", "country": "USA", "league": "NHL"},
            {"name": "Florida Panthers", "display_name": "Florida Panthers", "city": "Sunrise", "state": "Florida", "country": "USA", "league": "NHL"},
            {"name": "Montreal Canadiens", "display_name": "Montreal Canadiens", "city": "Montreal", "state": "Quebec", "country": "Canada", "league": "NHL"},
            {"name": "Ottawa Senators", "display_name": "Ottawa Senators", "city": "Ottawa", "state": "Ontario", "country": "Canada", "league": "NHL"},
            {"name": "Tampa Bay Lightning", "display_name": "Tampa Bay Lightning", "city": "Tampa", "state": "Florida", "country": "USA", "league": "NHL"},
            {"name": "Toronto Maple Leafs", "display_name": "Toronto Maple Leafs", "city": "Toronto", "state": "Ontario", "country": "Canada", "league": "NHL"},

            # NHL Teams - Eastern Conference Metropolitan Division
            {"name": "Carolina Hurricanes", "display_name": "Carolina Hurricanes", "city": "Raleigh", "state": "North Carolina", "country": "USA", "league": "NHL"},
            {"name": "Columbus Blue Jackets", "display_name": "Columbus Blue Jackets", "city": "Columbus", "state": "Ohio", "country": "USA", "league": "NHL"},
            {"name": "New Jersey Devils", "display_name": "New Jersey Devils", "city": "Newark", "state": "New Jersey", "country": "USA", "league": "NHL"},
            {"name": "New York Islanders", "display_name": "New York Islanders", "city": "Elmont", "state": "New York", "country": "USA", "league": "NHL"},
            {"name": "New York Rangers", "display_name": "New York Rangers", "city": "New York", "state": "New York", "country": "USA", "league": "NHL"},
            {"name": "Philadelphia Flyers", "display_name": "Philadelphia Flyers", "city": "Philadelphia", "state": "Pennsylvania", "country": "USA", "league": "NHL"},
            {"name": "Pittsburgh Penguins", "display_name": "Pittsburgh Penguins", "city": "Pittsburgh", "state": "Pennsylvania", "country": "USA", "league": "NHL"},
            {"name": "Washington Capitals", "display_name": "Washington Capitals", "city": "Washington", "state": "D.C.", "country": "USA", "league": "NHL"},

            # NHL Teams - Western Conference Central Division
            {"name": "Chicago Blackhawks", "display_name": "Chicago Blackhawks", "city": "Chicago", "state": "Illinois", "country": "USA", "league": "NHL"},
            {"name": "Colorado Avalanche", "display_name": "Colorado Avalanche", "city": "Denver", "state": "Colorado", "country": "USA", "league": "NHL"},
            {"name": "Dallas Stars", "display_name": "Dallas Stars", "city": "Dallas", "state": "Texas", "country": "USA", "league": "NHL"},
            {"name": "Minnesota Wild", "display_name": "Minnesota Wild", "city": "St. Paul", "state": "Minnesota", "country": "USA", "league": "NHL"},
            {"name": "Nashville Predators", "display_name": "Nashville Predators", "city": "Nashville", "state": "Tennessee", "country": "USA", "league": "NHL"},
            {"name": "St. Louis Blues", "display_name": "St. Louis Blues", "city": "St. Louis", "state": "Missouri", "country": "USA", "league": "NHL"},
            {"name": "Utah Hockey Club", "display_name": "Utah Hockey Club", "city": "Salt Lake City", "state": "Utah", "country": "USA", "league": "NHL"},
            {"name": "Winnipeg Jets", "display_name": "Winnipeg Jets", "city": "Winnipeg", "state": "Manitoba", "country": "Canada", "league": "NHL"},

            # NHL Teams - Western Conference Pacific Division
            {"name": "Anaheim Ducks", "display_name": "Anaheim Ducks", "city": "Anaheim", "state": "California", "country": "USA", "league": "NHL"},
            {"name": "Calgary Flames", "display_name": "Calgary Flames", "city": "Calgary", "state": "Alberta", "country": "Canada", "league": "NHL"},
            {"name": "Edmonton Oilers", "display_name": "Edmonton Oilers", "city": "Edmonton", "state": "Alberta", "country": "Canada", "league": "NHL"},
            {"name": "Los Angeles Kings", "display_name": "Los Angeles Kings", "city": "Los Angeles", "state": "California", "country": "USA", "league": "NHL"},
            {"name": "San Jose Sharks", "display_name": "San Jose Sharks", "city": "San Jose", "state": "California", "country": "USA", "league": "NHL"},
            {"name": "Seattle Kraken", "display_name": "Seattle Kraken", "city": "Seattle", "state": "Washington", "country": "USA", "league": "NHL"},
            {"name": "Vancouver Canucks", "display_name": "Vancouver Canucks", "city": "Vancouver", "state": "British Columbia", "country": "Canada", "league": "NHL"},
            {"name": "Vegas Golden Knights", "display_name": "Vegas Golden Knights", "city": "Las Vegas", "state": "Nevada", "country": "USA", "league": "NHL"},
        ]
    },
    {
        "name": "Soccer",
        "display_name": "Soccer/Football",
        "description": "Major League Soccer, Premier League, La Liga, Bundesliga, Serie A, and international soccer",
        "teams": [
            # Premier League (England)
            {"name": "Arsenal", "display_name": "Arsenal FC", "city": "London", "country": "England", "league": "Premier League"},
            {"name": "Aston Villa", "display_name": "Aston Villa FC", "city": "Birmingham", "country": "England", "league": "Premier League"},
            {"name": "Bournemouth", "display_name": "AFC Bournemouth", "city": "Bournemouth", "country": "England", "league": "Premier League"},
            {"name": "Brentford", "display_name": "Brentford FC", "city": "London", "country": "England", "league": "Premier League"},
            {"name": "Brighton & Hove Albion", "display_name": "Brighton & Hove Albion FC", "city": "Brighton", "country": "England", "league": "Premier League"},
            {"name": "Chelsea", "display_name": "Chelsea FC", "city": "London", "country": "England", "league": "Premier League"},
            {"name": "Crystal Palace", "display_name": "Crystal Palace FC", "city": "London", "country": "England", "league": "Premier League"},
            {"name": "Everton", "display_name": "Everton FC", "city": "Liverpool", "country": "England", "league": "Premier League"},
            {"name": "Fulham", "display_name": "Fulham FC", "city": "London", "country": "England", "league": "Premier League"},
            {"name": "Ipswich Town", "display_name": "Ipswich Town FC", "city": "Ipswich", "country": "England", "league": "Premier League"},
            {"name": "Leicester City", "display_name": "Leicester City FC", "city": "Leicester", "country": "England", "league": "Premier League"},
            {"name": "Liverpool", "display_name": "Liverpool FC", "city": "Liverpool", "country": "England", "league": "Premier League"},
            {"name": "Manchester City", "display_name": "Manchester City FC", "city": "Manchester", "country": "England", "league": "Premier League"},
            {"name": "Manchester United", "display_name": "Manchester United FC", "city": "Manchester", "country": "England", "league": "Premier League"},
            {"name": "Newcastle United", "display_name": "Newcastle United FC", "city": "Newcastle", "country": "England", "league": "Premier League"},
            {"name": "Nottingham Forest", "display_name": "Nottingham Forest FC", "city": "Nottingham", "country": "England", "league": "Premier League"},
            {"name": "Southampton", "display_name": "Southampton FC", "city": "Southampton", "country": "England", "league": "Premier League"},
            {"name": "Tottenham Hotspur", "display_name": "Tottenham Hotspur FC", "city": "London", "country": "England", "league": "Premier League"},
            {"name": "West Ham United", "display_name": "West Ham United FC", "city": "London", "country": "England", "league": "Premier League"},
            {"name": "Wolverhampton Wanderers", "display_name": "Wolverhampton Wanderers FC", "city": "Wolverhampton", "country": "England", "league": "Premier League"},

            # La Liga (Spain)
            {"name": "Athletic Bilbao", "display_name": "Athletic Club", "city": "Bilbao", "country": "Spain", "league": "La Liga"},
            {"name": "Atletico Madrid", "display_name": "Club Atletico de Madrid", "city": "Madrid", "country": "Spain", "league": "La Liga"},
            {"name": "FC Barcelona", "display_name": "FC Barcelona", "city": "Barcelona", "country": "Spain", "league": "La Liga"},
            {"name": "Real Madrid", "display_name": "Real Madrid CF", "city": "Madrid", "country": "Spain", "league": "La Liga"},
            {"name": "Sevilla", "display_name": "Sevilla FC", "city": "Seville", "country": "Spain", "league": "La Liga"},
            {"name": "Valencia", "display_name": "Valencia CF", "city": "Valencia", "country": "Spain", "league": "La Liga"},
            {"name": "Villarreal", "display_name": "Villarreal CF", "city": "Villarreal", "country": "Spain", "league": "La Liga"},

            # Bundesliga (Germany)
            {"name": "Bayern Munich", "display_name": "FC Bayern Munich", "city": "Munich", "country": "Germany", "league": "Bundesliga"},
            {"name": "Borussia Dortmund", "display_name": "Borussia Dortmund", "city": "Dortmund", "country": "Germany", "league": "Bundesliga"},
            {"name": "RB Leipzig", "display_name": "RB Leipzig", "city": "Leipzig", "country": "Germany", "league": "Bundesliga"},
            {"name": "Bayer Leverkusen", "display_name": "Bayer 04 Leverkusen", "city": "Leverkusen", "country": "Germany", "league": "Bundesliga"},
            {"name": "Eintracht Frankfurt", "display_name": "Eintracht Frankfurt", "city": "Frankfurt", "country": "Germany", "league": "Bundesliga"},

            # Serie A (Italy)
            {"name": "AC Milan", "display_name": "AC Milan", "city": "Milan", "country": "Italy", "league": "Serie A"},
            {"name": "Inter Milan", "display_name": "FC Internazionale Milano", "city": "Milan", "country": "Italy", "league": "Serie A"},
            {"name": "Juventus", "display_name": "Juventus FC", "city": "Turin", "country": "Italy", "league": "Serie A"},
            {"name": "AS Roma", "display_name": "AS Roma", "city": "Rome", "country": "Italy", "league": "Serie A"},
            {"name": "Napoli", "display_name": "SSC Napoli", "city": "Naples", "country": "Italy", "league": "Serie A"},

            # Major League Soccer (USA and Canada)
            {"name": "Atlanta United FC", "display_name": "Atlanta United FC", "city": "Atlanta", "state": "Georgia", "country": "USA", "league": "MLS"},
            {"name": "Austin FC", "display_name": "Austin FC", "city": "Austin", "state": "Texas", "country": "USA", "league": "MLS"},
            {"name": "Charlotte FC", "display_name": "Charlotte FC", "city": "Charlotte", "state": "North Carolina", "country": "USA", "league": "MLS"},
            {"name": "Chicago Fire FC", "display_name": "Chicago Fire FC", "city": "Chicago", "state": "Illinois", "country": "USA", "league": "MLS"},
            {"name": "FC Cincinnati", "display_name": "FC Cincinnati", "city": "Cincinnati", "state": "Ohio", "country": "USA", "league": "MLS"},
            {"name": "Colorado Rapids", "display_name": "Colorado Rapids", "city": "Commerce City", "state": "Colorado", "country": "USA", "league": "MLS"},
            {"name": "Columbus Crew", "display_name": "Columbus Crew", "city": "Columbus", "state": "Ohio", "country": "USA", "league": "MLS"},
            {"name": "D.C. United", "display_name": "D.C. United", "city": "Washington", "state": "D.C.", "country": "USA", "league": "MLS"},
            {"name": "FC Dallas", "display_name": "FC Dallas", "city": "Frisco", "state": "Texas", "country": "USA", "league": "MLS"},
            {"name": "Houston Dynamo FC", "display_name": "Houston Dynamo FC", "city": "Houston", "state": "Texas", "country": "USA", "league": "MLS"},
            {"name": "Inter Miami CF", "display_name": "Inter Miami CF", "city": "Fort Lauderdale", "state": "Florida", "country": "USA", "league": "MLS"},
            {"name": "LA Galaxy", "display_name": "LA Galaxy", "city": "Carson", "state": "California", "country": "USA", "league": "MLS"},
            {"name": "Los Angeles FC", "display_name": "Los Angeles FC", "city": "Los Angeles", "state": "California", "country": "USA", "league": "MLS"},
            {"name": "Minnesota United FC", "display_name": "Minnesota United FC", "city": "St. Paul", "state": "Minnesota", "country": "USA", "league": "MLS"},
            {"name": "CF Montreal", "display_name": "CF Montreal", "city": "Montreal", "state": "Quebec", "country": "Canada", "league": "MLS"},
            {"name": "Nashville SC", "display_name": "Nashville SC", "city": "Nashville", "state": "Tennessee", "country": "USA", "league": "MLS"},
            {"name": "New England Revolution", "display_name": "New England Revolution", "city": "Foxborough", "state": "Massachusetts", "country": "USA", "league": "MLS"},
            {"name": "New York City FC", "display_name": "New York City FC", "city": "New York", "state": "New York", "country": "USA", "league": "MLS"},
            {"name": "New York Red Bulls", "display_name": "New York Red Bulls", "city": "Harrison", "state": "New Jersey", "country": "USA", "league": "MLS"},
            {"name": "Orlando City SC", "display_name": "Orlando City SC", "city": "Orlando", "state": "Florida", "country": "USA", "league": "MLS"},
            {"name": "Philadelphia Union", "display_name": "Philadelphia Union", "city": "Chester", "state": "Pennsylvania", "country": "USA", "league": "MLS"},
            {"name": "Portland Timbers", "display_name": "Portland Timbers", "city": "Portland", "state": "Oregon", "country": "USA", "league": "MLS"},
            {"name": "Real Salt Lake", "display_name": "Real Salt Lake", "city": "Sandy", "state": "Utah", "country": "USA", "league": "MLS"},
            {"name": "San Jose Earthquakes", "display_name": "San Jose Earthquakes", "city": "San Jose", "state": "California", "country": "USA", "league": "MLS"},
            {"name": "Seattle Sounders FC", "display_name": "Seattle Sounders FC", "city": "Seattle", "state": "Washington", "country": "USA", "league": "MLS"},
            {"name": "Sporting Kansas City", "display_name": "Sporting Kansas City", "city": "Kansas City", "state": "Kansas", "country": "USA", "league": "MLS"},
            {"name": "St. Louis City SC", "display_name": "St. Louis City SC", "city": "St. Louis", "state": "Missouri", "country": "USA", "league": "MLS"},
            {"name": "Toronto FC", "display_name": "Toronto FC", "city": "Toronto", "state": "Ontario", "country": "Canada", "league": "MLS"},
            {"name": "Vancouver Whitecaps FC", "display_name": "Vancouver Whitecaps FC", "city": "Vancouver", "state": "British Columbia", "country": "Canada", "league": "MLS"},
        ]
    }
]


async def seed_comprehensive_teams_data():
    """Seed the database with comprehensive sports and teams data."""
    settings = Settings()
    db_manager = DatabaseManager(settings.database.url)

    try:
        async with db_manager.transaction() as session:
            # Clear existing data
            logger.info("Clearing existing sports and teams data...")
            from sqlalchemy import text
            await session.execute(text("DELETE FROM user_team_preferences"))
            await session.execute(text("DELETE FROM user_sport_preferences"))
            await session.execute(text("DELETE FROM teams"))
            await session.execute(text("DELETE FROM sports"))
            await session.commit()

            # Seed sports and teams
            for sport_data in COMPREHENSIVE_SPORTS_DATA:
                logger.info(f"Seeding sport: {sport_data['name']}")

                # Create sport
                sport = Sport(
                    name=sport_data["name"],
                    display_name=sport_data["display_name"],
                    description=sport_data["description"],
                    is_active=True
                )
                session.add(sport)
                await session.flush()  # Get the sport ID

                # Create teams for this sport
                team_count = 0
                for team_data in sport_data["teams"]:
                    team = Team(
                        sport_id=sport.id,
                        name=team_data["name"],
                        display_name=team_data["display_name"],
                        city=team_data.get("city"),
                        state=team_data.get("state"),
                        country=team_data.get("country"),
                        league=team_data.get("league"),
                        is_active=True
                    )
                    session.add(team)
                    team_count += 1

                logger.info(f"Added {team_count} teams for {sport_data['name']}")

            await session.commit()
            logger.info("Comprehensive sports and teams data seeded successfully!")

            # Log summary
            total_sports = len(COMPREHENSIVE_SPORTS_DATA)
            total_teams = sum(len(sport["teams"]) for sport in COMPREHENSIVE_SPORTS_DATA)
            logger.info(f"Summary: {total_sports} sports, {total_teams} teams added to database")

    except Exception as e:
        logger.error(f"Error seeding comprehensive sports data: {e}")
        raise
    finally:
        await db_manager.close()


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_comprehensive_teams_data())
