# Copyright (c) 2024 Sports Media Platform
# Licensed under the MIT License

"""Test user configuration for algorithm testing."""

from datetime import datetime
from typing import Any

# Static test user configuration for Dodgers MLB fan
TEST_USER_CONFIG = {
    "id": "test-user-dodgers-001",
    "email": "test.dodgers.fan@example.com",
    "username": "dodgers_test_user",
    "full_name": "Test Dodgers Fan",
    "is_active": True,
    "is_verified": True,

    # Team and sport preferences
    "favorite_teams": ["Los Angeles Dodgers", "Dodgers", "LAD"],
    "favorite_sports": ["mlb", "baseball"],

    # Content preferences
    "content_preferences": {
        "types": ["game_recap", "analysis", "breaking_news", "player_stats", "trade_news"],
        "sources": [],  # Will accept from all sources
        "keywords": [
            # Team variations
            "Dodgers", "Los Angeles Dodgers", "LAD", "LA Dodgers",
            # Stadium
            "Dodger Stadium",
            # Key players (update as needed)
            "Mookie Betts", "Freddie Freeman", "Julio Urías", "Walker Buehler",
            "Max Muncy", "Will Smith", "Trea Turner", "Chris Taylor",
            # Management
            "Dave Roberts", "Andrew Friedman",
            # League context
            "NL West", "National League", "World Series", "MLB playoffs"
        ]
    },

    # Quality and personalization settings
    "quality_threshold": 0.6,
    "personalization_score": 0.8,

    # Notification preferences
    "notification_settings": {
        "breaking_news": True,
        "game_updates": True,
        "trade_alerts": True,
        "injury_reports": True,
        "daily_digest": True
    },

    # Timestamps
    "created_at": datetime.now(),
    "updated_at": datetime.now(),
    "last_login": datetime.now()
}

# Team-specific filtering configuration
DODGERS_FILTER_CONFIG = {
    "primary_team": "Los Angeles Dodgers",
    "team_aliases": ["Dodgers", "Los Angeles Dodgers", "LAD", "LA Dodgers", "L.A. Dodgers"],
    "sport": "mlb",
    "league": "MLB",
    "division": "NL West",
    "rivals": ["San Francisco Giants", "Giants", "SF Giants", "San Diego Padres", "Padres"],
    "stadium": "Dodger Stadium",
    "city": "Los Angeles",
    "state": "California"
}

# Content scoring weights for Dodgers fan
CONTENT_SCORING_WEIGHTS = {
    "team_mention": 2.0,        # Direct team mention
    "player_mention": 1.5,      # Current player mention
    "rival_mention": 1.2,       # Rival team mention
    "league_context": 1.0,      # MLB/NL West context
    "breaking_news": 1.8,       # Breaking news multiplier
    "game_recap": 1.6,          # Game recap multiplier
    "trade_news": 1.7,          # Trade news multiplier
    "injury_report": 1.4,       # Injury report multiplier
    "analysis": 1.3,            # Analysis piece multiplier
    "quality_bonus": 1.2        # High quality content bonus
}

def get_test_user_config() -> dict[str, Any]:
    """Get the test user configuration."""
    return TEST_USER_CONFIG.copy()

def get_dodgers_filter_config() -> dict[str, Any]:
    """Get the Dodgers-specific filtering configuration."""
    return DODGERS_FILTER_CONFIG.copy()

def get_content_scoring_weights() -> dict[str, float]:
    """Get content scoring weights for personalization."""
    return CONTENT_SCORING_WEIGHTS.copy()

def is_dodgers_relevant_content(title: str, text: str, keywords: list[str] = None) -> bool:
    """Check if content is relevant to Dodgers fans."""
    content = f"{title} {text or ''}".lower()

    # Check for team mentions
    team_aliases = [alias.lower() for alias in DODGERS_FILTER_CONFIG["team_aliases"]]
    for alias in team_aliases:
        if alias.lower() in content:
            return True

    # Check for stadium mention
    if DODGERS_FILTER_CONFIG["stadium"].lower() in content:
        return True

    # Check for specific Dodgers players or management
    dodgers_keywords = [kw.lower() for kw in TEST_USER_CONFIG["content_preferences"]["keywords"]]
    for keyword in dodgers_keywords:
        if keyword.lower() in content and keyword.lower() not in ["mlb", "national league", "nl west", "world series", "mlb playoffs"]:
            return True

    # Check keywords if provided
    if keywords:
        content_keywords = [kw.lower() for kw in keywords if kw]
        test_keywords = [kw.lower() for kw in TEST_USER_CONFIG["content_preferences"]["keywords"]]

        for keyword in content_keywords:
            if any(test_kw in keyword or keyword in test_kw for test_kw in test_keywords):
                return True

    return False

def calculate_relevance_score(title: str, text: str, keywords: list[str] = None,
                            content_type: str = None) -> float:
    """Calculate relevance score for Dodgers fan."""
    if not is_dodgers_relevant_content(title, text, keywords):
        return 0.0

    content = f"{title} {text or ''}".lower()
    score = 0.0
    weights = get_content_scoring_weights()

    # Team mention scoring
    team_aliases = [alias.lower() for alias in DODGERS_FILTER_CONFIG["team_aliases"]]
    for alias in team_aliases:
        if alias in content:
            score += weights["team_mention"]
            break

    # Player mention scoring
    test_keywords = [kw.lower() for kw in TEST_USER_CONFIG["content_preferences"]["keywords"]]
    for keyword in test_keywords:
        if keyword.lower() in content:
            score += weights["player_mention"]
            break

    # Rival mention scoring
    rivals = [rival.lower() for rival in DODGERS_FILTER_CONFIG["rivals"]]
    for rival in rivals:
        if rival in content:
            score += weights["rival_mention"]
            break

    # Content type scoring
    if content_type and content_type in weights:
        score *= weights[content_type]

    # Normalize score (0.0 to 1.0)
    return min(score / 10.0, 1.0)
