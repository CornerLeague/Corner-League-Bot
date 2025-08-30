from typing import List
from datetime import datetime
from libs.auth.user_service import UserProfile
from libs.common.questionnaire_models import (
    UserSportPreference, 
    UserTeamPreference,
    Sport,
    Team
)

# Auth Response Mappers
def map_user_profile_to_response(profile: UserProfile) -> dict:
    """Convert UserProfile service model to API response format."""
    return {
        "user_id": profile.user_id,
        "email": profile.email,
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "roles": profile.roles,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
    }

# Questionnaire Response Mappers
def map_user_sport_preference_to_response(preference: UserSportPreference) -> dict:
    """Convert UserSportPreference model to API response format."""
    return {
        "id": preference.id,
        "user_id": preference.user_id,
        "sport_id": preference.sport_id,
        "sport_name": preference.sport.name if preference.sport else None,
        "interest_level": preference.interest_level,
        "created_at": preference.created_at.isoformat() if preference.created_at else None
    }

def map_user_team_preference_to_response(preference: UserTeamPreference) -> dict:
    """Convert UserTeamPreference model to API response format."""
    return {
        "id": preference.id,
        "user_id": preference.user_id,
        "team_id": preference.team_id,
        "team_name": preference.team.name if preference.team else None,
        "sport_name": preference.team.sport.name if preference.team and preference.team.sport else None,
        "interest_level": preference.interest_level,
        "created_at": preference.created_at.isoformat() if preference.created_at else None
    }

def map_sport_to_response(sport: Sport) -> dict:
    """Convert Sport model to API response format."""
    return {
        "id": sport.id,
        "name": sport.name,
        "display_name": sport.display_name,
        "description": sport.description,
        "is_active": sport.is_active
    }

def map_team_to_response(team: Team) -> dict:
    """Convert Team model to API response format."""
    return {
        "id": team.id,
        "name": team.name,
        "display_name": team.display_name,
        "sport_id": team.sport_id,
        "sport_name": team.sport.name if team.sport else None,
        "city": team.city,
        "state": team.state,
        "country": team.country,
        "league": team.league,
        "is_active": team.is_active
    }

def map_content_item_to_response(item) -> dict:
    """Convert ContentItem model to API response format."""
    return {
        "id": item.id,
        "title": item.title,
        "url": item.url,
        "source_name": item.source.name if item.source else None,
        "published_at": item.published_at.isoformat() if item.published_at else None,
        "quality_score": item.quality_score,
        "summary": item.summary,
        "content_type": item.content_type,
        "tags": item.tags
    }

def map_user_stats_to_response(stats) -> dict:
    """Convert user stats to API response format."""
    return {
        "articles_read": getattr(stats, 'articles_read', 0),
        "articles_saved": getattr(stats, 'articles_saved', 0),
        "articles_shared": getattr(stats, 'articles_shared', 0),
        "total_reading_time": getattr(stats, 'total_reading_time', 0),
        "favorite_topics": getattr(stats, 'favorite_topics', []),
        "activity_streak": getattr(stats, 'activity_streak', 0)
    }
