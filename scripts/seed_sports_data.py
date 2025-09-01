#!/usr/bin/env python3
"""
Seed the database with sports and teams data for the questionnaire.
"""

import asyncio
import logging

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
        "description": "Professional basketball including NBA and WNBA",
        "display_order": 1,
        "teams": [
            # NBA Teams - All 30 Teams
            # Eastern Conference - Atlantic Division
            {"name": "Boston Celtics", "slug": "celtics", "city": "Boston", "abbreviation": "BOS", "league": "NBA", "conference": "Eastern", "division": "Atlantic"},
            {"name": "Brooklyn Nets", "slug": "nets", "city": "Brooklyn", "abbreviation": "BKN", "league": "NBA", "conference": "Eastern", "division": "Atlantic"},
            {"name": "New York Knicks", "slug": "knicks", "city": "New York", "abbreviation": "NYK", "league": "NBA", "conference": "Eastern", "division": "Atlantic"},
            {"name": "Philadelphia 76ers", "slug": "76ers", "city": "Philadelphia", "abbreviation": "PHI", "league": "NBA", "conference": "Eastern", "division": "Atlantic"},
            {"name": "Toronto Raptors", "slug": "raptors", "city": "Toronto", "abbreviation": "TOR", "league": "NBA", "conference": "Eastern", "division": "Atlantic"},
            # Eastern Conference - Central Division
            {"name": "Chicago Bulls", "slug": "bulls", "city": "Chicago", "abbreviation": "CHI", "league": "NBA", "conference": "Eastern", "division": "Central"},
            {"name": "Cleveland Cavaliers", "slug": "cavaliers", "city": "Cleveland", "abbreviation": "CLE", "league": "NBA", "conference": "Eastern", "division": "Central"},
            {"name": "Detroit Pistons", "slug": "pistons", "city": "Detroit", "abbreviation": "DET", "league": "NBA", "conference": "Eastern", "division": "Central"},
            {"name": "Indiana Pacers", "slug": "pacers", "city": "Indiana", "abbreviation": "IND", "league": "NBA", "conference": "Eastern", "division": "Central"},
            {"name": "Milwaukee Bucks", "slug": "bucks", "city": "Milwaukee", "abbreviation": "MIL", "league": "NBA", "conference": "Eastern", "division": "Central"},
            # Eastern Conference - Southeast Division
            {"name": "Atlanta Hawks", "slug": "hawks", "city": "Atlanta", "abbreviation": "ATL", "league": "NBA", "conference": "Eastern", "division": "Southeast"},
            {"name": "Charlotte Hornets", "slug": "hornets", "city": "Charlotte", "abbreviation": "CHA", "league": "NBA", "conference": "Eastern", "division": "Southeast"},
            {"name": "Miami Heat", "slug": "heat", "city": "Miami", "abbreviation": "MIA", "league": "NBA", "conference": "Eastern", "division": "Southeast"},
            {"name": "Orlando Magic", "slug": "magic", "city": "Orlando", "abbreviation": "ORL", "league": "NBA", "conference": "Eastern", "division": "Southeast"},
            {"name": "Washington Wizards", "slug": "wizards", "city": "Washington", "abbreviation": "WAS", "league": "NBA", "conference": "Eastern", "division": "Southeast"},
            # Western Conference - Northwest Division
            {"name": "Denver Nuggets", "slug": "nuggets", "city": "Denver", "abbreviation": "DEN", "league": "NBA", "conference": "Western", "division": "Northwest"},
            {"name": "Minnesota Timberwolves", "slug": "timberwolves", "city": "Minnesota", "abbreviation": "MIN", "league": "NBA", "conference": "Western", "division": "Northwest"},
            {"name": "Oklahoma City Thunder", "slug": "thunder", "city": "Oklahoma City", "abbreviation": "OKC", "league": "NBA", "conference": "Western", "division": "Northwest"},
            {"name": "Portland Trail Blazers", "slug": "trail-blazers", "city": "Portland", "abbreviation": "POR", "league": "NBA", "conference": "Western", "division": "Northwest"},
            {"name": "Utah Jazz", "slug": "jazz", "city": "Utah", "abbreviation": "UTA", "league": "NBA", "conference": "Western", "division": "Northwest"},
            # Western Conference - Pacific Division
            {"name": "Golden State Warriors", "slug": "warriors", "city": "Golden State", "abbreviation": "GSW", "league": "NBA", "conference": "Western", "division": "Pacific"},
            {"name": "Los Angeles Clippers", "slug": "clippers", "city": "Los Angeles", "abbreviation": "LAC", "league": "NBA", "conference": "Western", "division": "Pacific"},
            {"name": "Los Angeles Lakers", "slug": "lakers", "city": "Los Angeles", "abbreviation": "LAL", "league": "NBA", "conference": "Western", "division": "Pacific"},
            {"name": "Phoenix Suns", "slug": "suns", "city": "Phoenix", "abbreviation": "PHX", "league": "NBA", "conference": "Western", "division": "Pacific"},
            {"name": "Sacramento Kings", "slug": "kings", "city": "Sacramento", "abbreviation": "SAC", "league": "NBA", "conference": "Western", "division": "Pacific"},
            # Western Conference - Southwest Division
            {"name": "Dallas Mavericks", "slug": "mavericks", "city": "Dallas", "abbreviation": "DAL", "league": "NBA", "conference": "Western", "division": "Southwest"},
            {"name": "Houston Rockets", "slug": "rockets", "city": "Houston", "abbreviation": "HOU", "league": "NBA", "conference": "Western", "division": "Southwest"},
            {"name": "Memphis Grizzlies", "slug": "grizzlies", "city": "Memphis", "abbreviation": "MEM", "league": "NBA", "conference": "Western", "division": "Southwest"},
            {"name": "New Orleans Pelicans", "slug": "pelicans", "city": "New Orleans", "abbreviation": "NOP", "league": "NBA", "conference": "Western", "division": "Southwest"},
            {"name": "San Antonio Spurs", "slug": "spurs", "city": "San Antonio", "abbreviation": "SAS", "league": "NBA", "conference": "Western", "division": "Southwest"},
        ]
    },
    {
        "name": "Football (American)",
        "slug": "football",
        "has_teams": True,
        "description": "American football including NFL",
        "display_order": 2,
        "teams": [
            # AFC East
            {"name": "Buffalo Bills", "slug": "bills", "city": "Buffalo", "abbreviation": "BUF", "league": "NFL", "conference": "AFC", "division": "East"},
            {"name": "Miami Dolphins", "slug": "dolphins", "city": "Miami", "abbreviation": "MIA", "league": "NFL", "conference": "AFC", "division": "East"},
            {"name": "New England Patriots", "slug": "patriots", "city": "New England", "abbreviation": "NE", "league": "NFL", "conference": "AFC", "division": "East"},
            {"name": "New York Jets", "slug": "jets", "city": "New York", "abbreviation": "NYJ", "league": "NFL", "conference": "AFC", "division": "East"},

            # AFC North
            {"name": "Baltimore Ravens", "slug": "ravens", "city": "Baltimore", "abbreviation": "BAL", "league": "NFL", "conference": "AFC", "division": "North"},
            {"name": "Cincinnati Bengals", "slug": "bengals", "city": "Cincinnati", "abbreviation": "CIN", "league": "NFL", "conference": "AFC", "division": "North"},
            {"name": "Cleveland Browns", "slug": "browns", "city": "Cleveland", "abbreviation": "CLE", "league": "NFL", "conference": "AFC", "division": "North"},
            {"name": "Pittsburgh Steelers", "slug": "steelers", "city": "Pittsburgh", "abbreviation": "PIT", "league": "NFL", "conference": "AFC", "division": "North"},

            # AFC South
            {"name": "Houston Texans", "slug": "texans", "city": "Houston", "abbreviation": "HOU", "league": "NFL", "conference": "AFC", "division": "South"},
            {"name": "Indianapolis Colts", "slug": "colts", "city": "Indianapolis", "abbreviation": "IND", "league": "NFL", "conference": "AFC", "division": "South"},
            {"name": "Jacksonville Jaguars", "slug": "jaguars", "city": "Jacksonville", "abbreviation": "JAX", "league": "NFL", "conference": "AFC", "division": "South"},
            {"name": "Tennessee Titans", "slug": "titans", "city": "Tennessee", "abbreviation": "TEN", "league": "NFL", "conference": "AFC", "division": "South"},

            # AFC West
            {"name": "Denver Broncos", "slug": "broncos", "city": "Denver", "abbreviation": "DEN", "league": "NFL", "conference": "AFC", "division": "West"},
            {"name": "Kansas City Chiefs", "slug": "chiefs", "city": "Kansas City", "abbreviation": "KC", "league": "NFL", "conference": "AFC", "division": "West"},
            {"name": "Las Vegas Raiders", "slug": "raiders", "city": "Las Vegas", "abbreviation": "LV", "league": "NFL", "conference": "AFC", "division": "West"},
            {"name": "Los Angeles Chargers", "slug": "chargers", "city": "Los Angeles", "abbreviation": "LAC", "league": "NFL", "conference": "AFC", "division": "West"},

            # NFC East
            {"name": "Dallas Cowboys", "slug": "cowboys", "city": "Dallas", "abbreviation": "DAL", "league": "NFL", "conference": "NFC", "division": "East"},
            {"name": "New York Giants", "slug": "giants", "city": "New York", "abbreviation": "NYG", "league": "NFL", "conference": "NFC", "division": "East"},
            {"name": "Philadelphia Eagles", "slug": "eagles", "city": "Philadelphia", "abbreviation": "PHI", "league": "NFL", "conference": "NFC", "division": "East"},
            {"name": "Washington Commanders", "slug": "commanders", "city": "Washington", "abbreviation": "WAS", "league": "NFL", "conference": "NFC", "division": "East"},

            # NFC North
            {"name": "Chicago Bears", "slug": "bears", "city": "Chicago", "abbreviation": "CHI", "league": "NFL", "conference": "NFC", "division": "North"},
            {"name": "Detroit Lions", "slug": "lions", "city": "Detroit", "abbreviation": "DET", "league": "NFL", "conference": "NFC", "division": "North"},
            {"name": "Green Bay Packers", "slug": "packers", "city": "Green Bay", "abbreviation": "GB", "league": "NFL", "conference": "NFC", "division": "North"},
            {"name": "Minnesota Vikings", "slug": "vikings", "city": "Minnesota", "abbreviation": "MIN", "league": "NFL", "conference": "NFC", "division": "North"},

            # NFC South
            {"name": "Atlanta Falcons", "slug": "falcons", "city": "Atlanta", "abbreviation": "ATL", "league": "NFL", "conference": "NFC", "division": "South"},
            {"name": "Carolina Panthers", "slug": "panthers", "city": "Carolina", "abbreviation": "CAR", "league": "NFL", "conference": "NFC", "division": "South"},
            {"name": "New Orleans Saints", "slug": "saints", "city": "New Orleans", "abbreviation": "NO", "league": "NFL", "conference": "NFC", "division": "South"},
            {"name": "Tampa Bay Buccaneers", "slug": "buccaneers", "city": "Tampa Bay", "abbreviation": "TB", "league": "NFL", "conference": "NFC", "division": "South"},

            # NFC West
            {"name": "Arizona Cardinals", "slug": "cardinals", "city": "Arizona", "abbreviation": "ARI", "league": "NFL", "conference": "NFC", "division": "West"},
            {"name": "Los Angeles Rams", "slug": "rams", "city": "Los Angeles", "abbreviation": "LAR", "league": "NFL", "conference": "NFC", "division": "West"},
            {"name": "San Francisco 49ers", "slug": "49ers", "city": "San Francisco", "abbreviation": "SF", "league": "NFL", "conference": "NFC", "division": "West"},
            {"name": "Seattle Seahawks", "slug": "seahawks", "city": "Seattle", "abbreviation": "SEA", "league": "NFL", "conference": "NFC", "division": "West"},
        ]
    },
    {
        "name": "Baseball",
        "slug": "baseball",
        "has_teams": True,
        "description": "Major League Baseball",
        "display_order": 3,
        "teams": [
            # MLB Teams - All 30 Teams
            # American League - East Division
            {"name": "Baltimore Orioles", "slug": "orioles", "city": "Baltimore", "abbreviation": "BAL", "league": "MLB", "conference": "American League", "division": "East"},
            {"name": "Boston Red Sox", "slug": "red-sox", "city": "Boston", "abbreviation": "BOS", "league": "MLB", "conference": "American League", "division": "East"},
            {"name": "New York Yankees", "slug": "yankees", "city": "New York", "abbreviation": "NYY", "league": "MLB", "conference": "American League", "division": "East"},
            {"name": "Tampa Bay Rays", "slug": "rays", "city": "Tampa Bay", "abbreviation": "TB", "league": "MLB", "conference": "American League", "division": "East"},
            {"name": "Toronto Blue Jays", "slug": "blue-jays", "city": "Toronto", "abbreviation": "TOR", "league": "MLB", "conference": "American League", "division": "East"},
            # American League - Central Division
            {"name": "Chicago White Sox", "slug": "white-sox", "city": "Chicago", "abbreviation": "CWS", "league": "MLB", "conference": "American League", "division": "Central"},
            {"name": "Cleveland Guardians", "slug": "guardians", "city": "Cleveland", "abbreviation": "CLE", "league": "MLB", "conference": "American League", "division": "Central"},
            {"name": "Detroit Tigers", "slug": "tigers", "city": "Detroit", "abbreviation": "DET", "league": "MLB", "conference": "American League", "division": "Central"},
            {"name": "Kansas City Royals", "slug": "royals", "city": "Kansas City", "abbreviation": "KC", "league": "MLB", "conference": "American League", "division": "Central"},
            {"name": "Minnesota Twins", "slug": "twins", "city": "Minnesota", "abbreviation": "MIN", "league": "MLB", "conference": "American League", "division": "Central"},
            # American League - West Division
            {"name": "Houston Astros", "slug": "astros", "city": "Houston", "abbreviation": "HOU", "league": "MLB", "conference": "American League", "division": "West"},
            {"name": "Los Angeles Angels", "slug": "angels", "city": "Los Angeles", "abbreviation": "LAA", "league": "MLB", "conference": "American League", "division": "West"},
            {"name": "Oakland Athletics", "slug": "athletics", "city": "Oakland", "abbreviation": "OAK", "league": "MLB", "conference": "American League", "division": "West"},
            {"name": "Seattle Mariners", "slug": "mariners", "city": "Seattle", "abbreviation": "SEA", "league": "MLB", "conference": "American League", "division": "West"},
            {"name": "Texas Rangers", "slug": "rangers", "city": "Texas", "abbreviation": "TEX", "league": "MLB", "conference": "American League", "division": "West"},
            # National League - East Division
            {"name": "Atlanta Braves", "slug": "braves", "city": "Atlanta", "abbreviation": "ATL", "league": "MLB", "conference": "National League", "division": "East"},
            {"name": "Miami Marlins", "slug": "marlins", "city": "Miami", "abbreviation": "MIA", "league": "MLB", "conference": "National League", "division": "East"},
            {"name": "New York Mets", "slug": "mets", "city": "New York", "abbreviation": "NYM", "league": "MLB", "conference": "National League", "division": "East"},
            {"name": "Philadelphia Phillies", "slug": "phillies", "city": "Philadelphia", "abbreviation": "PHI", "league": "MLB", "conference": "National League", "division": "East"},
            {"name": "Washington Nationals", "slug": "nationals", "city": "Washington", "abbreviation": "WSH", "league": "MLB", "conference": "National League", "division": "East"},
            # National League - Central Division
            {"name": "Chicago Cubs", "slug": "cubs", "city": "Chicago", "abbreviation": "CHC", "league": "MLB", "conference": "National League", "division": "Central"},
            {"name": "Cincinnati Reds", "slug": "reds", "city": "Cincinnati", "abbreviation": "CIN", "league": "MLB", "conference": "National League", "division": "Central"},
            {"name": "Milwaukee Brewers", "slug": "brewers", "city": "Milwaukee", "abbreviation": "MIL", "league": "MLB", "conference": "National League", "division": "Central"},
            {"name": "Pittsburgh Pirates", "slug": "pirates", "city": "Pittsburgh", "abbreviation": "PIT", "league": "MLB", "conference": "National League", "division": "Central"},
            {"name": "St. Louis Cardinals", "slug": "cardinals", "city": "St. Louis", "abbreviation": "STL", "league": "MLB", "conference": "National League", "division": "Central"},
            # National League - West Division
            {"name": "Arizona Diamondbacks", "slug": "diamondbacks", "city": "Arizona", "abbreviation": "ARI", "league": "MLB", "conference": "National League", "division": "West"},
            {"name": "Colorado Rockies", "slug": "rockies", "city": "Colorado", "abbreviation": "COL", "league": "MLB", "conference": "National League", "division": "West"},
            {"name": "Los Angeles Dodgers", "slug": "dodgers", "city": "Los Angeles", "abbreviation": "LAD", "league": "MLB", "conference": "National League", "division": "West"},
            {"name": "San Diego Padres", "slug": "padres", "city": "San Diego", "abbreviation": "SD", "league": "MLB", "conference": "National League", "division": "West"},
            {"name": "San Francisco Giants", "slug": "giants", "city": "San Francisco", "abbreviation": "SF", "league": "MLB", "conference": "National League", "division": "West"},
        ]
    },
    {
        "name": "Soccer/Football (International)",
        "slug": "soccer",
        "has_teams": True,
        "description": "Major League Soccer, Premier League, and international soccer",
        "display_order": 4,
        "teams": [
            # Premier League
            {"name": "Arsenal", "slug": "arsenal", "city": "London", "abbreviation": "ARS", "league": "Premier League"},
            {"name": "Aston Villa", "slug": "aston-villa", "city": "Birmingham", "abbreviation": "AVL", "league": "Premier League"},
            {"name": "Bournemouth", "slug": "bournemouth", "city": "Bournemouth", "abbreviation": "BOU", "league": "Premier League"},
            {"name": "Brentford", "slug": "brentford", "city": "London", "abbreviation": "BRE", "league": "Premier League"},
            {"name": "Brighton & Hove Albion", "slug": "brighton", "city": "Brighton", "abbreviation": "BHA", "league": "Premier League"},
            {"name": "Chelsea", "slug": "chelsea", "city": "London", "abbreviation": "CHE", "league": "Premier League"},
            {"name": "Crystal Palace", "slug": "crystal-palace", "city": "London", "abbreviation": "CRY", "league": "Premier League"},
            {"name": "Everton", "slug": "everton", "city": "Liverpool", "abbreviation": "EVE", "league": "Premier League"},
            {"name": "Fulham", "slug": "fulham", "city": "London", "abbreviation": "FUL", "league": "Premier League"},
            {"name": "Ipswich Town", "slug": "ipswich-town", "city": "Ipswich", "abbreviation": "IPS", "league": "Premier League"},
            {"name": "Leicester City", "slug": "leicester-city", "city": "Leicester", "abbreviation": "LEI", "league": "Premier League"},
            {"name": "Liverpool", "slug": "liverpool", "city": "Liverpool", "abbreviation": "LIV", "league": "Premier League"},
            {"name": "Manchester City", "slug": "manchester-city", "city": "Manchester", "abbreviation": "MCI", "league": "Premier League"},
            {"name": "Manchester United", "slug": "manchester-united", "city": "Manchester", "abbreviation": "MUN", "league": "Premier League"},
            {"name": "Newcastle United", "slug": "newcastle-united", "city": "Newcastle", "abbreviation": "NEW", "league": "Premier League"},
            {"name": "Nottingham Forest", "slug": "nottingham-forest", "city": "Nottingham", "abbreviation": "NFO", "league": "Premier League"},
            {"name": "Southampton", "slug": "southampton", "city": "Southampton", "abbreviation": "SOU", "league": "Premier League"},
            {"name": "Tottenham Hotspur", "slug": "tottenham", "city": "London", "abbreviation": "TOT", "league": "Premier League"},
            {"name": "West Ham United", "slug": "west-ham", "city": "London", "abbreviation": "WHU", "league": "Premier League"},
            {"name": "Wolverhampton Wanderers", "slug": "wolves", "city": "Wolverhampton", "abbreviation": "WOL", "league": "Premier League"},
            # UEFA Champions League (unique teams not in other leagues)
            {"name": "Paris Saint-Germain", "slug": "psg", "city": "Paris", "abbreviation": "PSG", "league": "UEFA Champions League"},
            {"name": "Ajax", "slug": "ajax", "city": "Amsterdam", "abbreviation": "AJA", "league": "UEFA Champions League"},
            {"name": "Benfica", "slug": "benfica", "city": "Lisbon", "abbreviation": "BEN", "league": "UEFA Champions League"},
            {"name": "Porto", "slug": "porto", "city": "Porto", "abbreviation": "POR", "league": "UEFA Champions League"},
            # MLS
            {"name": "Atlanta United FC", "slug": "atlanta-united", "city": "Atlanta", "abbreviation": "ATL", "league": "MLS"},
            {"name": "Austin FC", "slug": "austin-fc", "city": "Austin", "abbreviation": "ATX", "league": "MLS"},
            {"name": "Charlotte FC", "slug": "charlotte-fc", "city": "Charlotte", "abbreviation": "CLT", "league": "MLS"},
            {"name": "Chicago Fire FC", "slug": "chicago-fire", "city": "Chicago", "abbreviation": "CHI", "league": "MLS"},
            {"name": "FC Cincinnati", "slug": "fc-cincinnati", "city": "Cincinnati", "abbreviation": "CIN", "league": "MLS"},
            {"name": "Colorado Rapids", "slug": "colorado-rapids", "city": "Commerce City", "abbreviation": "COL", "league": "MLS"},
            {"name": "Columbus Crew", "slug": "columbus-crew", "city": "Columbus", "abbreviation": "CLB", "league": "MLS"},
            {"name": "D.C. United", "slug": "dc-united", "city": "Washington", "abbreviation": "DC", "league": "MLS"},
            {"name": "FC Dallas", "slug": "fc-dallas", "city": "Frisco", "abbreviation": "DAL", "league": "MLS"},
            {"name": "Houston Dynamo FC", "slug": "houston-dynamo", "city": "Houston", "abbreviation": "HOU", "league": "MLS"},
            {"name": "Inter Miami CF", "slug": "inter-miami", "city": "Fort Lauderdale", "abbreviation": "MIA", "league": "MLS"},
            {"name": "LA Galaxy", "slug": "la-galaxy", "city": "Carson", "abbreviation": "LAG", "league": "MLS"},
            {"name": "Los Angeles FC", "slug": "lafc", "city": "Los Angeles", "abbreviation": "LAFC", "league": "MLS"},
            {"name": "Minnesota United FC", "slug": "minnesota-united", "city": "Saint Paul", "abbreviation": "MIN", "league": "MLS"},
            {"name": "CF Montréal", "slug": "cf-montreal", "city": "Montreal", "abbreviation": "MTL", "league": "MLS"},
            {"name": "Nashville SC", "slug": "nashville-sc", "city": "Nashville", "abbreviation": "NSH", "league": "MLS"},
            {"name": "New England Revolution", "slug": "new-england-revolution", "city": "Foxborough", "abbreviation": "NE", "league": "MLS"},
            {"name": "New York City FC", "slug": "nycfc", "city": "New York City", "abbreviation": "NYC", "league": "MLS"},
            {"name": "New York Red Bulls", "slug": "ny-red-bulls", "city": "Harrison", "abbreviation": "NYRB", "league": "MLS"},
            {"name": "Orlando City SC", "slug": "orlando-city", "city": "Orlando", "abbreviation": "ORL", "league": "MLS"},
            {"name": "Philadelphia Union", "slug": "philadelphia-union", "city": "Chester", "abbreviation": "PHI", "league": "MLS"},
            {"name": "Portland Timbers", "slug": "portland-timbers", "city": "Portland", "abbreviation": "POR", "league": "MLS"},
            {"name": "Real Salt Lake", "slug": "real-salt-lake", "city": "Sandy", "abbreviation": "RSL", "league": "MLS"},
            {"name": "San Jose Earthquakes", "slug": "san-jose-earthquakes", "city": "San Jose", "abbreviation": "SJ", "league": "MLS"},
            {"name": "Seattle Sounders FC", "slug": "seattle-sounders", "city": "Seattle", "abbreviation": "SEA", "league": "MLS"},
            {"name": "Sporting Kansas City", "slug": "sporting-kc", "city": "Kansas City", "abbreviation": "SKC", "league": "MLS"},
            {"name": "St. Louis City SC", "slug": "st-louis-city", "city": "St. Louis", "abbreviation": "STL", "league": "MLS"},
            {"name": "Toronto FC", "slug": "toronto-fc", "city": "Toronto", "abbreviation": "TOR", "league": "MLS"},
            {"name": "Vancouver Whitecaps FC", "slug": "vancouver-whitecaps", "city": "Vancouver", "abbreviation": "VAN", "league": "MLS"},
            # La Liga
            {"name": "Athletic Bilbao", "slug": "athletic-bilbao", "city": "Bilbao", "abbreviation": "ATH", "league": "La Liga"},
            {"name": "Atletico Madrid", "slug": "atletico-madrid", "city": "Madrid", "abbreviation": "ATM", "league": "La Liga"},
            {"name": "Barcelona", "slug": "barcelona", "city": "Barcelona", "abbreviation": "BAR", "league": "La Liga"},
            {"name": "Celta Vigo", "slug": "celta-vigo", "city": "Vigo", "abbreviation": "CEL", "league": "La Liga"},
            {"name": "Getafe", "slug": "getafe", "city": "Getafe", "abbreviation": "GET", "league": "La Liga"},
            {"name": "Girona", "slug": "girona", "city": "Girona", "abbreviation": "GIR", "league": "La Liga"},
            {"name": "Las Palmas", "slug": "las-palmas", "city": "Las Palmas", "abbreviation": "LPA", "league": "La Liga"},
            {"name": "Leganes", "slug": "leganes", "city": "Leganes", "abbreviation": "LEG", "league": "La Liga"},
            {"name": "Mallorca", "slug": "mallorca", "city": "Palma", "abbreviation": "MLL", "league": "La Liga"},
            {"name": "Osasuna", "slug": "osasuna", "city": "Pamplona", "abbreviation": "OSA", "league": "La Liga"},
            {"name": "Rayo Vallecano", "slug": "rayo-vallecano", "city": "Madrid", "abbreviation": "RAY", "league": "La Liga"},
            {"name": "Real Betis", "slug": "real-betis", "city": "Seville", "abbreviation": "BET", "league": "La Liga"},
            {"name": "Real Madrid", "slug": "real-madrid", "city": "Madrid", "abbreviation": "RMA", "league": "La Liga"},
            {"name": "Real Sociedad", "slug": "real-sociedad", "city": "San Sebastian", "abbreviation": "RSO", "league": "La Liga"},
            {"name": "Sevilla", "slug": "sevilla", "city": "Seville", "abbreviation": "SEV", "league": "La Liga"},
            {"name": "Valencia", "slug": "valencia", "city": "Valencia", "abbreviation": "VAL", "league": "La Liga"},
            {"name": "Valladolid", "slug": "valladolid", "city": "Valladolid", "abbreviation": "VLL", "league": "La Liga"},
            {"name": "Villarreal", "slug": "villarreal", "city": "Villarreal", "abbreviation": "VIL", "league": "La Liga"},
            {"name": "Alaves", "slug": "alaves", "city": "Vitoria-Gasteiz", "abbreviation": "ALA", "league": "La Liga"},
            {"name": "Espanyol", "slug": "espanyol", "city": "Barcelona", "abbreviation": "ESP", "league": "La Liga"},
            # Bundesliga
            {"name": "FC Augsburg", "slug": "fc-augsburg", "city": "Augsburg", "abbreviation": "AUG", "league": "Bundesliga"},
            {"name": "Bayer Leverkusen", "slug": "bayer-leverkusen", "city": "Leverkusen", "abbreviation": "B04", "league": "Bundesliga"},
            {"name": "Bayern Munich", "slug": "bayern-munich", "city": "Munich", "abbreviation": "FCB", "league": "Bundesliga"},
            {"name": "VfL Bochum", "slug": "vfl-bochum", "city": "Bochum", "abbreviation": "BOC", "league": "Bundesliga"},
            {"name": "Borussia Dortmund", "slug": "borussia-dortmund", "city": "Dortmund", "abbreviation": "BVB", "league": "Bundesliga"},
            {"name": "Borussia Monchengladbach", "slug": "borussia-monchengladbach", "city": "Monchengladbach", "abbreviation": "BMG", "league": "Bundesliga"},
            {"name": "Eintracht Frankfurt", "slug": "eintracht-frankfurt", "city": "Frankfurt", "abbreviation": "SGE", "league": "Bundesliga"},
            {"name": "SC Freiburg", "slug": "sc-freiburg", "city": "Freiburg", "abbreviation": "SCF", "league": "Bundesliga"},
            {"name": "1. FC Heidenheim", "slug": "fc-heidenheim", "city": "Heidenheim", "abbreviation": "HDH", "league": "Bundesliga"},
            {"name": "TSG Hoffenheim", "slug": "tsg-hoffenheim", "city": "Sinsheim", "abbreviation": "HOF", "league": "Bundesliga"},
            {"name": "Holstein Kiel", "slug": "holstein-kiel", "city": "Kiel", "abbreviation": "KIE", "league": "Bundesliga"},
            {"name": "RB Leipzig", "slug": "rb-leipzig", "city": "Leipzig", "abbreviation": "RBL", "league": "Bundesliga"},
            {"name": "1. FSV Mainz 05", "slug": "fsv-mainz-05", "city": "Mainz", "abbreviation": "M05", "league": "Bundesliga"},
            {"name": "FC St. Pauli", "slug": "fc-st-pauli", "city": "Hamburg", "abbreviation": "STP", "league": "Bundesliga"},
            {"name": "1. FC Union Berlin", "slug": "fc-union-berlin", "city": "Berlin", "abbreviation": "FCU", "league": "Bundesliga"},
            {"name": "VfB Stuttgart", "slug": "vfb-stuttgart", "city": "Stuttgart", "abbreviation": "VFB", "league": "Bundesliga"},
            {"name": "SV Werder Bremen", "slug": "sv-werder-bremen", "city": "Bremen", "abbreviation": "SVW", "league": "Bundesliga"},
            {"name": "VfL Wolfsburg", "slug": "vfl-wolfsburg", "city": "Wolfsburg", "abbreviation": "WOB", "league": "Bundesliga"},
            # Serie A
            {"name": "Atalanta", "slug": "atalanta", "city": "Bergamo", "abbreviation": "ATA", "league": "Serie A"},
            {"name": "Bologna", "slug": "bologna", "city": "Bologna", "abbreviation": "BOL", "league": "Serie A"},
            {"name": "Cagliari", "slug": "cagliari", "city": "Cagliari", "abbreviation": "CAG", "league": "Serie A"},
            {"name": "Como", "slug": "como", "city": "Como", "abbreviation": "COM", "league": "Serie A"},
            {"name": "Empoli", "slug": "empoli", "city": "Empoli", "abbreviation": "EMP", "league": "Serie A"},
            {"name": "Fiorentina", "slug": "fiorentina", "city": "Florence", "abbreviation": "FIO", "league": "Serie A"},
            {"name": "Genoa", "slug": "genoa", "city": "Genoa", "abbreviation": "GEN", "league": "Serie A"},
            {"name": "Hellas Verona", "slug": "hellas-verona", "city": "Verona", "abbreviation": "HVR", "league": "Serie A"},
            {"name": "Inter Milan", "slug": "inter-milan", "city": "Milan", "abbreviation": "INT", "league": "Serie A"},
            {"name": "Juventus", "slug": "juventus", "city": "Turin", "abbreviation": "JUV", "league": "Serie A"},
            {"name": "Lazio", "slug": "lazio", "city": "Rome", "abbreviation": "LAZ", "league": "Serie A"},
            {"name": "Lecce", "slug": "lecce", "city": "Lecce", "abbreviation": "LEC", "league": "Serie A"},
            {"name": "AC Milan", "slug": "ac-milan", "city": "Milan", "abbreviation": "MIL", "league": "Serie A"},
            {"name": "Monza", "slug": "monza", "city": "Monza", "abbreviation": "MON", "league": "Serie A"},
            {"name": "Napoli", "slug": "napoli", "city": "Naples", "abbreviation": "NAP", "league": "Serie A"},
            {"name": "Parma", "slug": "parma", "city": "Parma", "abbreviation": "PAR", "league": "Serie A"},
            {"name": "AS Roma", "slug": "as-roma", "city": "Rome", "abbreviation": "ROM", "league": "Serie A"},
            {"name": "Torino", "slug": "torino", "city": "Turin", "abbreviation": "TOR", "league": "Serie A"},
            {"name": "Udinese", "slug": "udinese", "city": "Udine", "abbreviation": "UDI", "league": "Serie A"},
            {"name": "Venezia", "slug": "venezia", "city": "Venice", "abbreviation": "VEN", "league": "Serie A"}
        ]
    },
    {
        "name": "Hockey",
        "slug": "hockey",
        "has_teams": True,
        "description": "National Hockey League and international hockey",
        "display_order": 5,
        "teams": [
            # NHL - Eastern Conference - Atlantic Division
            {"name": "Boston Bruins", "slug": "bruins", "city": "Boston", "abbreviation": "BOS", "league": "NHL", "conference": "Eastern", "division": "Atlantic"},
            {"name": "Buffalo Sabres", "slug": "sabres", "city": "Buffalo", "abbreviation": "BUF", "league": "NHL", "conference": "Eastern", "division": "Atlantic"},
            {"name": "Detroit Red Wings", "slug": "red-wings", "city": "Detroit", "abbreviation": "DET", "league": "NHL", "conference": "Eastern", "division": "Atlantic"},
            {"name": "Florida Panthers", "slug": "panthers", "city": "Florida", "abbreviation": "FLA", "league": "NHL", "conference": "Eastern", "division": "Atlantic"},
            {"name": "Montreal Canadiens", "slug": "canadiens", "city": "Montreal", "abbreviation": "MTL", "league": "NHL", "conference": "Eastern", "division": "Atlantic"},
            {"name": "Ottawa Senators", "slug": "senators", "city": "Ottawa", "abbreviation": "OTT", "league": "NHL", "conference": "Eastern", "division": "Atlantic"},
            {"name": "Tampa Bay Lightning", "slug": "lightning", "city": "Tampa Bay", "abbreviation": "TB", "league": "NHL", "conference": "Eastern", "division": "Atlantic"},
            {"name": "Toronto Maple Leafs", "slug": "maple-leafs", "city": "Toronto", "abbreviation": "TOR", "league": "NHL", "conference": "Eastern", "division": "Atlantic"},
            # NHL - Eastern Conference - Metropolitan Division
            {"name": "Carolina Hurricanes", "slug": "hurricanes", "city": "Carolina", "abbreviation": "CAR", "league": "NHL", "conference": "Eastern", "division": "Metropolitan"},
            {"name": "Columbus Blue Jackets", "slug": "blue-jackets", "city": "Columbus", "abbreviation": "CBJ", "league": "NHL", "conference": "Eastern", "division": "Metropolitan"},
            {"name": "New Jersey Devils", "slug": "devils", "city": "New Jersey", "abbreviation": "NJ", "league": "NHL", "conference": "Eastern", "division": "Metropolitan"},
            {"name": "New York Islanders", "slug": "islanders", "city": "New York", "abbreviation": "NYI", "league": "NHL", "conference": "Eastern", "division": "Metropolitan"},
            {"name": "New York Rangers", "slug": "rangers", "city": "New York", "abbreviation": "NYR", "league": "NHL", "conference": "Eastern", "division": "Metropolitan"},
            {"name": "Philadelphia Flyers", "slug": "flyers", "city": "Philadelphia", "abbreviation": "PHI", "league": "NHL", "conference": "Eastern", "division": "Metropolitan"},
            {"name": "Pittsburgh Penguins", "slug": "penguins", "city": "Pittsburgh", "abbreviation": "PIT", "league": "NHL", "conference": "Eastern", "division": "Metropolitan"},
            {"name": "Washington Capitals", "slug": "capitals", "city": "Washington", "abbreviation": "WSH", "league": "NHL", "conference": "Eastern", "division": "Metropolitan"},
            # NHL - Western Conference - Central Division
            {"name": "Arizona Coyotes", "slug": "coyotes", "city": "Arizona", "abbreviation": "ARI", "league": "NHL", "conference": "Western", "division": "Central"},
            {"name": "Chicago Blackhawks", "slug": "blackhawks", "city": "Chicago", "abbreviation": "CHI", "league": "NHL", "conference": "Western", "division": "Central"},
            {"name": "Colorado Avalanche", "slug": "avalanche", "city": "Colorado", "abbreviation": "COL", "league": "NHL", "conference": "Western", "division": "Central"},
            {"name": "Dallas Stars", "slug": "stars", "city": "Dallas", "abbreviation": "DAL", "league": "NHL", "conference": "Western", "division": "Central"},
            {"name": "Minnesota Wild", "slug": "wild", "city": "Minnesota", "abbreviation": "MIN", "league": "NHL", "conference": "Western", "division": "Central"},
            {"name": "Nashville Predators", "slug": "predators", "city": "Nashville", "abbreviation": "NSH", "league": "NHL", "conference": "Western", "division": "Central"},
            {"name": "St. Louis Blues", "slug": "blues", "city": "St. Louis", "abbreviation": "STL", "league": "NHL", "conference": "Western", "division": "Central"},
            {"name": "Winnipeg Jets", "slug": "jets", "city": "Winnipeg", "abbreviation": "WPG", "league": "NHL", "conference": "Western", "division": "Central"},
            # NHL - Western Conference - Pacific Division
            {"name": "Anaheim Ducks", "slug": "ducks", "city": "Anaheim", "abbreviation": "ANA", "league": "NHL", "conference": "Western", "division": "Pacific"},
            {"name": "Calgary Flames", "slug": "flames", "city": "Calgary", "abbreviation": "CGY", "league": "NHL", "conference": "Western", "division": "Pacific"},
            {"name": "Edmonton Oilers", "slug": "oilers", "city": "Edmonton", "abbreviation": "EDM", "league": "NHL", "conference": "Western", "division": "Pacific"},
            {"name": "Los Angeles Kings", "slug": "kings", "city": "Los Angeles", "abbreviation": "LAK", "league": "NHL", "conference": "Western", "division": "Pacific"},
            {"name": "San Jose Sharks", "slug": "sharks", "city": "San Jose", "abbreviation": "SJ", "league": "NHL", "conference": "Western", "division": "Pacific"},
            {"name": "Seattle Kraken", "slug": "kraken", "city": "Seattle", "abbreviation": "SEA", "league": "NHL", "conference": "Western", "division": "Pacific"},
            {"name": "Vancouver Canucks", "slug": "canucks", "city": "Vancouver", "abbreviation": "VAN", "league": "NHL", "conference": "Western", "division": "Pacific"},
            {"name": "Vegas Golden Knights", "slug": "golden-knights", "city": "Las Vegas", "abbreviation": "VGK", "league": "NHL", "conference": "Western", "division": "Pacific"},
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
        "name": "College Basketball",
        "slug": "college-basketball",
        "has_teams": True,
        "description": "NCAA Division I men's and women's college basketball",
        "display_order": 13,
        "teams": [
            # ACC Conference
            {"name": "Duke Blue Devils", "slug": "duke", "city": "Durham", "abbreviation": "DUKE", "league": "NCAA", "conference": "ACC"},
            {"name": "North Carolina Tar Heels", "slug": "unc", "city": "Chapel Hill", "abbreviation": "UNC", "league": "NCAA", "conference": "ACC"},
            {"name": "Virginia Cavaliers", "slug": "virginia", "city": "Charlottesville", "abbreviation": "UVA", "league": "NCAA", "conference": "ACC"},
            {"name": "Miami Hurricanes", "slug": "miami", "city": "Miami", "abbreviation": "MIA", "league": "NCAA", "conference": "ACC"},
            {"name": "Florida State Seminoles", "slug": "florida-state", "city": "Tallahassee", "abbreviation": "FSU", "league": "NCAA", "conference": "ACC"},
            {"name": "Syracuse Orange", "slug": "syracuse", "city": "Syracuse", "abbreviation": "SYR", "league": "NCAA", "conference": "ACC"},
            {"name": "Louisville Cardinals", "slug": "louisville", "city": "Louisville", "abbreviation": "LOU", "league": "NCAA", "conference": "ACC"},
            {"name": "Clemson Tigers", "slug": "clemson", "city": "Clemson", "abbreviation": "CLEM", "league": "NCAA", "conference": "ACC"},

            # SEC Conference
            {"name": "Kentucky Wildcats", "slug": "kentucky", "city": "Lexington", "abbreviation": "UK", "league": "NCAA", "conference": "SEC"},
            {"name": "Tennessee Volunteers", "slug": "tennessee", "city": "Knoxville", "abbreviation": "TENN", "league": "NCAA", "conference": "SEC"},
            {"name": "Auburn Tigers", "slug": "auburn", "city": "Auburn", "abbreviation": "AUB", "league": "NCAA", "conference": "SEC"},
            {"name": "Alabama Crimson Tide", "slug": "alabama", "city": "Tuscaloosa", "abbreviation": "ALA", "league": "NCAA", "conference": "SEC"},
            {"name": "Arkansas Razorbacks", "slug": "arkansas", "city": "Fayetteville", "abbreviation": "ARK", "league": "NCAA", "conference": "SEC"},
            {"name": "Florida Gators", "slug": "florida", "city": "Gainesville", "abbreviation": "FLA", "league": "NCAA", "conference": "SEC"},
            {"name": "LSU Tigers", "slug": "lsu", "city": "Baton Rouge", "abbreviation": "LSU", "league": "NCAA", "conference": "SEC"},
            {"name": "Mississippi State Bulldogs", "slug": "mississippi-state", "city": "Starkville", "abbreviation": "MSU", "league": "NCAA", "conference": "SEC"},

            # Big 12 Conference
            {"name": "Kansas Jayhawks", "slug": "kansas", "city": "Lawrence", "abbreviation": "KU", "league": "NCAA", "conference": "Big 12"},
            {"name": "Baylor Bears", "slug": "baylor", "city": "Waco", "abbreviation": "BAY", "league": "NCAA", "conference": "Big 12"},
            {"name": "Texas Tech Red Raiders", "slug": "texas-tech", "city": "Lubbock", "abbreviation": "TTU", "league": "NCAA", "conference": "Big 12"},
            {"name": "Texas Longhorns", "slug": "texas", "city": "Austin", "abbreviation": "TEX", "league": "NCAA", "conference": "Big 12"},
            {"name": "Oklahoma Sooners", "slug": "oklahoma", "city": "Norman", "abbreviation": "OU", "league": "NCAA", "conference": "Big 12"},
            {"name": "Iowa State Cyclones", "slug": "iowa-state", "city": "Ames", "abbreviation": "ISU", "league": "NCAA", "conference": "Big 12"},

            # Big Ten Conference
            {"name": "Michigan State Spartans", "slug": "michigan-state", "city": "East Lansing", "abbreviation": "MSU", "league": "NCAA", "conference": "Big Ten"},
            {"name": "Michigan Wolverines", "slug": "michigan", "city": "Ann Arbor", "abbreviation": "MICH", "league": "NCAA", "conference": "Big Ten"},
            {"name": "Ohio State Buckeyes", "slug": "ohio-state", "city": "Columbus", "abbreviation": "OSU", "league": "NCAA", "conference": "Big Ten"},
            {"name": "Indiana Hoosiers", "slug": "indiana", "city": "Bloomington", "abbreviation": "IU", "league": "NCAA", "conference": "Big Ten"},
            {"name": "Purdue Boilermakers", "slug": "purdue", "city": "West Lafayette", "abbreviation": "PUR", "league": "NCAA", "conference": "Big Ten"},
            {"name": "Wisconsin Badgers", "slug": "wisconsin", "city": "Madison", "abbreviation": "WIS", "league": "NCAA", "conference": "Big Ten"},
            {"name": "Illinois Fighting Illini", "slug": "illinois", "city": "Champaign", "abbreviation": "ILL", "league": "NCAA", "conference": "Big Ten"},
            {"name": "Iowa Hawkeyes", "slug": "iowa", "city": "Iowa City", "abbreviation": "IOWA", "league": "NCAA", "conference": "Big Ten"},

            # Pac-12 Conference
            {"name": "UCLA Bruins", "slug": "ucla", "city": "Los Angeles", "abbreviation": "UCLA", "league": "NCAA", "conference": "Pac-12"},
            {"name": "USC Trojans", "slug": "usc", "city": "Los Angeles", "abbreviation": "USC", "league": "NCAA", "conference": "Pac-12"},
            {"name": "Arizona Wildcats", "slug": "arizona", "city": "Tucson", "abbreviation": "ARIZ", "league": "NCAA", "conference": "Pac-12"},
            {"name": "Oregon Ducks", "slug": "oregon", "city": "Eugene", "abbreviation": "ORE", "league": "NCAA", "conference": "Pac-12"},
            {"name": "Stanford Cardinal", "slug": "stanford", "city": "Stanford", "abbreviation": "STAN", "league": "NCAA", "conference": "Pac-12"},
            {"name": "Washington Huskies", "slug": "washington", "city": "Seattle", "abbreviation": "WASH", "league": "NCAA", "conference": "Pac-12"},

            # Big East Conference
            {"name": "Villanova Wildcats", "slug": "villanova", "city": "Villanova", "abbreviation": "NOVA", "league": "NCAA", "conference": "Big East"},
            {"name": "Georgetown Hoyas", "slug": "georgetown", "city": "Washington", "abbreviation": "GTOWN", "league": "NCAA", "conference": "Big East"},
            {"name": "Marquette Golden Eagles", "slug": "marquette", "city": "Milwaukee", "abbreviation": "MARQ", "league": "NCAA", "conference": "Big East"},
            {"name": "Creighton Bluejays", "slug": "creighton", "city": "Omaha", "abbreviation": "CREI", "league": "NCAA", "conference": "Big East"},
            {"name": "Providence Friars", "slug": "providence", "city": "Providence", "abbreviation": "PROV", "league": "NCAA", "conference": "Big East"},

            # Other Major Programs
            {"name": "Gonzaga Bulldogs", "slug": "gonzaga", "city": "Spokane", "abbreviation": "GONZ", "league": "NCAA", "conference": "WCC"},
            {"name": "Saint Mary's Gaels", "slug": "saint-marys", "city": "Moraga", "abbreviation": "SMC", "league": "NCAA", "conference": "WCC"},
            {"name": "Houston Cougars", "slug": "houston", "city": "Houston", "abbreviation": "HOU", "league": "NCAA", "conference": "AAC"},
            {"name": "Memphis Tigers", "slug": "memphis", "city": "Memphis", "abbreviation": "MEM", "league": "NCAA", "conference": "AAC"},
            {"name": "Cincinnati Bearcats", "slug": "cincinnati", "city": "Cincinnati", "abbreviation": "CIN", "league": "NCAA", "conference": "AAC"},
            {"name": "Wichita State Shockers", "slug": "wichita-state", "city": "Wichita", "abbreviation": "WSU", "league": "NCAA", "conference": "AAC"},
            {"name": "San Diego State Aztecs", "slug": "san-diego-state", "city": "San Diego", "abbreviation": "SDSU", "league": "NCAA", "conference": "Mountain West"},
            {"name": "Nevada Wolf Pack", "slug": "nevada", "city": "Reno", "abbreviation": "NEV", "league": "NCAA", "conference": "Mountain West"},
        ]
    },
    {
        "name": "College Football",
        "slug": "college-football",
        "has_teams": True,
        "description": "NCAA Division I FBS college football",
        "display_order": 14,
        "teams": [
            # SEC Conference
            {"name": "Alabama Crimson Tide", "slug": "alabama", "city": "Tuscaloosa", "abbreviation": "ALA", "league": "NCAA", "conference": "SEC"},
            {"name": "Georgia Bulldogs", "slug": "georgia", "city": "Athens", "abbreviation": "UGA", "league": "NCAA", "conference": "SEC"},
            {"name": "LSU Tigers", "slug": "lsu", "city": "Baton Rouge", "abbreviation": "LSU", "league": "NCAA", "conference": "SEC"},
            {"name": "Florida Gators", "slug": "florida", "city": "Gainesville", "abbreviation": "FLA", "league": "NCAA", "conference": "SEC"},
            {"name": "Auburn Tigers", "slug": "auburn", "city": "Auburn", "abbreviation": "AUB", "league": "NCAA", "conference": "SEC"},
            {"name": "Tennessee Volunteers", "slug": "tennessee", "city": "Knoxville", "abbreviation": "TENN", "league": "NCAA", "conference": "SEC"},
            {"name": "Kentucky Wildcats", "slug": "kentucky", "city": "Lexington", "abbreviation": "UK", "league": "NCAA", "conference": "SEC"},
            {"name": "South Carolina Gamecocks", "slug": "south-carolina", "city": "Columbia", "abbreviation": "SC", "league": "NCAA", "conference": "SEC"},
            {"name": "Arkansas Razorbacks", "slug": "arkansas", "city": "Fayetteville", "abbreviation": "ARK", "league": "NCAA", "conference": "SEC"},
            {"name": "Mississippi State Bulldogs", "slug": "mississippi-state", "city": "Starkville", "abbreviation": "MSU", "league": "NCAA", "conference": "SEC"},
            {"name": "Ole Miss Rebels", "slug": "ole-miss", "city": "Oxford", "abbreviation": "MISS", "league": "NCAA", "conference": "SEC"},
            {"name": "Missouri Tigers", "slug": "missouri", "city": "Columbia", "abbreviation": "MIZ", "league": "NCAA", "conference": "SEC"},
            {"name": "Vanderbilt Commodores", "slug": "vanderbilt", "city": "Nashville", "abbreviation": "VU", "league": "NCAA", "conference": "SEC"},
            {"name": "Texas A&M Aggies", "slug": "texas-am", "city": "College Station", "abbreviation": "TAMU", "league": "NCAA", "conference": "SEC"},

            # Big Ten Conference
            {"name": "Ohio State Buckeyes", "slug": "ohio-state", "city": "Columbus", "abbreviation": "OSU", "league": "NCAA", "conference": "Big Ten"},
            {"name": "Michigan Wolverines", "slug": "michigan", "city": "Ann Arbor", "abbreviation": "MICH", "league": "NCAA", "conference": "Big Ten"},
            {"name": "Penn State Nittany Lions", "slug": "penn-state", "city": "University Park", "abbreviation": "PSU", "league": "NCAA", "conference": "Big Ten"},
            {"name": "Michigan State Spartans", "slug": "michigan-state", "city": "East Lansing", "abbreviation": "MSU", "league": "NCAA", "conference": "Big Ten"},
            {"name": "Wisconsin Badgers", "slug": "wisconsin", "city": "Madison", "abbreviation": "WIS", "league": "NCAA", "conference": "Big Ten"},
            {"name": "Iowa Hawkeyes", "slug": "iowa", "city": "Iowa City", "abbreviation": "IOWA", "league": "NCAA", "conference": "Big Ten"},
            {"name": "Minnesota Golden Gophers", "slug": "minnesota", "city": "Minneapolis", "abbreviation": "MINN", "league": "NCAA", "conference": "Big Ten"},
            {"name": "Nebraska Cornhuskers", "slug": "nebraska", "city": "Lincoln", "abbreviation": "NEB", "league": "NCAA", "conference": "Big Ten"},
            {"name": "Illinois Fighting Illini", "slug": "illinois", "city": "Champaign", "abbreviation": "ILL", "league": "NCAA", "conference": "Big Ten"},
            {"name": "Indiana Hoosiers", "slug": "indiana", "city": "Bloomington", "abbreviation": "IU", "league": "NCAA", "conference": "Big Ten"},
            {"name": "Purdue Boilermakers", "slug": "purdue", "city": "West Lafayette", "abbreviation": "PUR", "league": "NCAA", "conference": "Big Ten"},
            {"name": "Northwestern Wildcats", "slug": "northwestern", "city": "Evanston", "abbreviation": "NU", "league": "NCAA", "conference": "Big Ten"},
            {"name": "Maryland Terrapins", "slug": "maryland", "city": "College Park", "abbreviation": "MD", "league": "NCAA", "conference": "Big Ten"},
            {"name": "Rutgers Scarlet Knights", "slug": "rutgers", "city": "New Brunswick", "abbreviation": "RU", "league": "NCAA", "conference": "Big Ten"},

            # ACC Conference
            {"name": "Clemson Tigers", "slug": "clemson", "city": "Clemson", "abbreviation": "CLEM", "league": "NCAA", "conference": "ACC"},
            {"name": "Florida State Seminoles", "slug": "florida-state", "city": "Tallahassee", "abbreviation": "FSU", "league": "NCAA", "conference": "ACC"},
            {"name": "Miami Hurricanes", "slug": "miami", "city": "Miami", "abbreviation": "MIA", "league": "NCAA", "conference": "ACC"},
            {"name": "North Carolina Tar Heels", "slug": "unc", "city": "Chapel Hill", "abbreviation": "UNC", "league": "NCAA", "conference": "ACC"},
            {"name": "NC State Wolfpack", "slug": "nc-state", "city": "Raleigh", "abbreviation": "NCSU", "league": "NCAA", "conference": "ACC"},
            {"name": "Duke Blue Devils", "slug": "duke", "city": "Durham", "abbreviation": "DUKE", "league": "NCAA", "conference": "ACC"},
            {"name": "Wake Forest Demon Deacons", "slug": "wake-forest", "city": "Winston-Salem", "abbreviation": "WAKE", "league": "NCAA", "conference": "ACC"},
            {"name": "Virginia Tech Hokies", "slug": "virginia-tech", "city": "Blacksburg", "abbreviation": "VT", "league": "NCAA", "conference": "ACC"},
            {"name": "Virginia Cavaliers", "slug": "virginia", "city": "Charlottesville", "abbreviation": "UVA", "league": "NCAA", "conference": "ACC"},
            {"name": "Pittsburgh Panthers", "slug": "pittsburgh", "city": "Pittsburgh", "abbreviation": "PITT", "league": "NCAA", "conference": "ACC"},
            {"name": "Louisville Cardinals", "slug": "louisville", "city": "Louisville", "abbreviation": "LOU", "league": "NCAA", "conference": "ACC"},
            {"name": "Syracuse Orange", "slug": "syracuse", "city": "Syracuse", "abbreviation": "SYR", "league": "NCAA", "conference": "ACC"},
            {"name": "Boston College Eagles", "slug": "boston-college", "city": "Chestnut Hill", "abbreviation": "BC", "league": "NCAA", "conference": "ACC"},
            {"name": "Georgia Tech Yellow Jackets", "slug": "georgia-tech", "city": "Atlanta", "abbreviation": "GT", "league": "NCAA", "conference": "ACC"},

            # Big 12 Conference
            {"name": "Texas Longhorns", "slug": "texas", "city": "Austin", "abbreviation": "TEX", "league": "NCAA", "conference": "Big 12"},
            {"name": "Oklahoma Sooners", "slug": "oklahoma", "city": "Norman", "abbreviation": "OU", "league": "NCAA", "conference": "Big 12"},
            {"name": "Oklahoma State Cowboys", "slug": "oklahoma-state", "city": "Stillwater", "abbreviation": "OKST", "league": "NCAA", "conference": "Big 12"},
            {"name": "Baylor Bears", "slug": "baylor", "city": "Waco", "abbreviation": "BAY", "league": "NCAA", "conference": "Big 12"},
            {"name": "TCU Horned Frogs", "slug": "tcu", "city": "Fort Worth", "abbreviation": "TCU", "league": "NCAA", "conference": "Big 12"},
            {"name": "Texas Tech Red Raiders", "slug": "texas-tech", "city": "Lubbock", "abbreviation": "TTU", "league": "NCAA", "conference": "Big 12"},
            {"name": "Kansas Jayhawks", "slug": "kansas", "city": "Lawrence", "abbreviation": "KU", "league": "NCAA", "conference": "Big 12"},
            {"name": "Kansas State Wildcats", "slug": "kansas-state", "city": "Manhattan", "abbreviation": "KSU", "league": "NCAA", "conference": "Big 12"},
            {"name": "Iowa State Cyclones", "slug": "iowa-state", "city": "Ames", "abbreviation": "ISU", "league": "NCAA", "conference": "Big 12"},
            {"name": "West Virginia Mountaineers", "slug": "west-virginia", "city": "Morgantown", "abbreviation": "WVU", "league": "NCAA", "conference": "Big 12"},

            # Pac-12 Conference
            {"name": "USC Trojans", "slug": "usc", "city": "Los Angeles", "abbreviation": "USC", "league": "NCAA", "conference": "Pac-12"},
            {"name": "UCLA Bruins", "slug": "ucla", "city": "Los Angeles", "abbreviation": "UCLA", "league": "NCAA", "conference": "Pac-12"},
            {"name": "Oregon Ducks", "slug": "oregon", "city": "Eugene", "abbreviation": "ORE", "league": "NCAA", "conference": "Pac-12"},
            {"name": "Oregon State Beavers", "slug": "oregon-state", "city": "Corvallis", "abbreviation": "OSU", "league": "NCAA", "conference": "Pac-12"},
            {"name": "Washington Huskies", "slug": "washington", "city": "Seattle", "abbreviation": "WASH", "league": "NCAA", "conference": "Pac-12"},
            {"name": "Washington State Cougars", "slug": "washington-state", "city": "Pullman", "abbreviation": "WSU", "league": "NCAA", "conference": "Pac-12"},
            {"name": "Stanford Cardinal", "slug": "stanford", "city": "Stanford", "abbreviation": "STAN", "league": "NCAA", "conference": "Pac-12"},
            {"name": "California Golden Bears", "slug": "california", "city": "Berkeley", "abbreviation": "CAL", "league": "NCAA", "conference": "Pac-12"},
            {"name": "Arizona Wildcats", "slug": "arizona", "city": "Tucson", "abbreviation": "ARIZ", "league": "NCAA", "conference": "Pac-12"},
            {"name": "Arizona State Sun Devils", "slug": "arizona-state", "city": "Tempe", "abbreviation": "ASU", "league": "NCAA", "conference": "Pac-12"},
            {"name": "Utah Utes", "slug": "utah", "city": "Salt Lake City", "abbreviation": "UTAH", "league": "NCAA", "conference": "Pac-12"},
            {"name": "Colorado Buffaloes", "slug": "colorado", "city": "Boulder", "abbreviation": "CU", "league": "NCAA", "conference": "Pac-12"},

            # Notre Dame (Independent)
            {"name": "Notre Dame Fighting Irish", "slug": "notre-dame", "city": "South Bend", "abbreviation": "ND", "league": "NCAA", "conference": "Independent"},

            # Group of 5 - Top Programs
            {"name": "Cincinnati Bearcats", "slug": "cincinnati", "city": "Cincinnati", "abbreviation": "CIN", "league": "NCAA", "conference": "AAC"},
            {"name": "Houston Cougars", "slug": "houston", "city": "Houston", "abbreviation": "HOU", "league": "NCAA", "conference": "AAC"},
            {"name": "UCF Knights", "slug": "ucf", "city": "Orlando", "abbreviation": "UCF", "league": "NCAA", "conference": "AAC"},
            {"name": "Memphis Tigers", "slug": "memphis", "city": "Memphis", "abbreviation": "MEM", "league": "NCAA", "conference": "AAC"},
            {"name": "Boise State Broncos", "slug": "boise-state", "city": "Boise", "abbreviation": "BSU", "league": "NCAA", "conference": "Mountain West"},
            {"name": "San Diego State Aztecs", "slug": "san-diego-state", "city": "San Diego", "abbreviation": "SDSU", "league": "NCAA", "conference": "Mountain West"},
            {"name": "Fresno State Bulldogs", "slug": "fresno-state", "city": "Fresno", "abbreviation": "FSU", "league": "NCAA", "conference": "Mountain West"},
            {"name": "Coastal Carolina Chanticleers", "slug": "coastal-carolina", "city": "Conway", "abbreviation": "CCU", "league": "NCAA", "conference": "Sun Belt"},
            {"name": "Louisiana Ragin' Cajuns", "slug": "louisiana", "city": "Lafayette", "abbreviation": "UL", "league": "NCAA", "conference": "Sun Belt"},
            {"name": "App State Mountaineers", "slug": "app-state", "city": "Boone", "abbreviation": "APP", "league": "NCAA", "conference": "Sun Belt"},
        ]
    },
    {
        "name": "Olympics",
        "slug": "olympics",
        "has_teams": False,
        "description": "Summer and Winter Olympic Games coverage",
        "display_order": 15,
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
                    slug=sport_data["slug"],
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
                            slug=team_data["slug"],
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

    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_sports_data())
