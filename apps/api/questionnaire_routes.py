from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, text
from typing import List, Optional
from pydantic import BaseModel

from libs.auth.decorators import require_auth
from libs.common.database import get_db
from libs.common.questionnaire_models import (
    Sport, Team, UserSportPreference, UserTeamPreference
)
from libs.api.response import ApiResponse
from libs.api.mappers import (
    map_sport_to_response,
    map_team_to_response,
    map_user_sport_preference_to_response,
    map_user_team_preference_to_response
)

router = APIRouter()

# Response Models
class SportResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    is_active: bool

class TeamResponse(BaseModel):
    id: int
    name: str
    display_name: str
    sport_id: int
    sport_name: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    league: Optional[str]
    is_active: bool

class UserSportPreferenceResponse(BaseModel):
    id: int
    user_id: str
    sport_id: int
    sport_name: Optional[str]
    interest_level: int
    created_at: Optional[str]

class UserTeamPreferenceResponse(BaseModel):
    id: int
    user_id: str
    team_id: int
    team_name: Optional[str]
    sport_name: Optional[str]
    interest_level: int
    created_at: Optional[str]

class QuestionnaireStatusResponse(BaseModel):
    user_id: str
    sports_completed: bool
    teams_completed: bool
    total_sports_selected: int
    total_teams_selected: int
    completion_percentage: float

# Request Models
class SportPreferenceRequest(BaseModel):
    sport_id: int
    interest_level: int

class TeamPreferenceRequest(BaseModel):
    team_id: int
    interest_level: int

@router.get("/status", response_model=ApiResponse[QuestionnaireStatusResponse])
@require_auth
async def get_questionnaire_status(
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get questionnaire completion status for the current user with optimized query."""
    
    # Single optimized query using CTEs and joins
    query = text("""
        WITH sport_prefs AS (
            SELECT COUNT(*) as sport_count
            FROM user_sport_preferences usp
            JOIN sports s ON usp.sport_id = s.id
            WHERE usp.user_id = :user_id AND s.is_active = true
        ),
        team_prefs AS (
            SELECT COUNT(*) as team_count
            FROM user_team_preferences utp
            JOIN teams t ON utp.team_id = t.id
            JOIN sports s ON t.sport_id = s.id
            WHERE utp.user_id = :user_id AND t.is_active = true AND s.is_active = true
        ),
        user_status AS (
            SELECT 
                sp.sport_count,
                tp.team_count,
                CASE WHEN sp.sport_count >= 3 THEN true ELSE false END as sports_completed,
                CASE WHEN tp.team_count >= 5 THEN true ELSE false END as teams_completed
            FROM sport_prefs sp
            FULL OUTER JOIN team_prefs tp ON true
        )
        SELECT 
            sport_count,
            team_count,
            sports_completed,
            teams_completed,
            CASE 
                WHEN sports_completed AND teams_completed THEN 100.0
                WHEN sports_completed OR teams_completed THEN 50.0
                ELSE (sport_count * 16.67 + team_count * 10.0)
            END as completion_percentage
        FROM user_status
    """)
    
    result = db.execute(query, {"user_id": user_id}).fetchone()
    
    if not result:
        # No preferences found, return default status
        response_data = QuestionnaireStatusResponse(
            user_id=user_id,
            sports_completed=False,
            teams_completed=False,
            total_sports_selected=0,
            total_teams_selected=0,
            completion_percentage=0.0
        )
    else:
        response_data = QuestionnaireStatusResponse(
            user_id=user_id,
            sports_completed=bool(result.sports_completed),
            teams_completed=bool(result.teams_completed),
            total_sports_selected=result.sport_count or 0,
            total_teams_selected=result.team_count or 0,
            completion_percentage=float(result.completion_percentage or 0.0)
        )
    
    return ApiResponse.success(data=response_data)

@router.get("/sports", response_model=ApiResponse[List[SportResponse]])
async def get_available_sports(db: Session = Depends(get_db)):
    """Get all available sports."""
    
    # Use explicit select with where clause
    stmt = select(Sport).where(Sport.is_active == True).order_by(Sport.display_name)
    sports = db.execute(stmt).scalars().all()
    
    response_data = [map_sport_to_response(sport) for sport in sports]
    return ApiResponse.success(data=response_data)

@router.get("/teams", response_model=ApiResponse[List[TeamResponse]])
async def get_teams_by_sport(
    sport_id: int = Query(..., description="Sport ID to filter teams"),
    db: Session = Depends(get_db)
):
    """Get teams for a specific sport."""
    
    # Verify sport exists and is active
    sport_stmt = select(Sport).where(Sport.id == sport_id, Sport.is_active == True)
    sport = db.execute(sport_stmt).scalar_one_or_none()
    
    if not sport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sport with ID {sport_id} not found or inactive"
        )
    
    # Get teams for the sport with explicit join
    teams_stmt = (
        select(Team)
        .join(Sport, Team.sport_id == Sport.id)
        .where(
            Team.sport_id == sport_id,
            Team.is_active == True,
            Sport.is_active == True
        )
        .order_by(Team.display_name)
    )
    teams = db.execute(teams_stmt).scalars().all()
    
    response_data = [map_team_to_response(team) for team in teams]
    return ApiResponse.success(data=response_data)

@router.post("/sports/preferences", response_model=ApiResponse[List[UserSportPreferenceResponse]])
@require_auth
async def save_sport_preferences(
    preferences: List[SportPreferenceRequest],
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Save user sport preferences."""
    
    # Validate interest levels
    for pref in preferences:
        if not 1 <= pref.interest_level <= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Interest level must be between 1 and 5, got {pref.interest_level}"
            )
    
    # Validate sport IDs exist and are active
    sport_ids = [pref.sport_id for pref in preferences]
    sports_stmt = select(Sport).where(Sport.id.in_(sport_ids), Sport.is_active == True)
    existing_sports = db.execute(sports_stmt).scalars().all()
    existing_sport_ids = {sport.id for sport in existing_sports}
    
    invalid_sport_ids = set(sport_ids) - existing_sport_ids
    if invalid_sport_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or inactive sport IDs: {list(invalid_sport_ids)}"
        )
    
    # Delete existing preferences
    delete_stmt = delete(UserSportPreference).where(UserSportPreference.user_id == user_id)
    db.execute(delete_stmt)
    
    # Add new preferences
    new_preferences = []
    for pref in preferences:
        new_pref = UserSportPreference(
            user_id=user_id,
            sport_id=pref.sport_id,
            interest_level=pref.interest_level
        )
        db.add(new_pref)
        new_preferences.append(new_pref)
    
    db.commit()
    
    # Refresh to get relationships loaded
    for pref in new_preferences:
        db.refresh(pref)
    
    response_data = [map_user_sport_preference_to_response(pref) for pref in new_preferences]
    return ApiResponse.success(data=response_data)

@router.post("/teams/preferences", response_model=ApiResponse[List[UserTeamPreferenceResponse]])
@require_auth
async def save_team_preferences(
    preferences: List[TeamPreferenceRequest],
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Save user team preferences."""
    
    # Validate interest levels
    for pref in preferences:
        if not 1 <= pref.interest_level <= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Interest level must be between 1 and 5, got {pref.interest_level}"
            )
    
    # Validate team IDs exist and are active with explicit join
    team_ids = [pref.team_id for pref in preferences]
    teams_stmt = (
        select(Team)
        .join(Sport, Team.sport_id == Sport.id)
        .where(
            Team.id.in_(team_ids),
            Team.is_active == True,
            Sport.is_active == True
        )
    )
    existing_teams = db.execute(teams_stmt).scalars().all()
    existing_team_ids = {team.id for team in existing_teams}
    
    invalid_team_ids = set(team_ids) - existing_team_ids
    if invalid_team_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or inactive team IDs: {list(invalid_team_ids)}"
        )
    
    # Delete existing preferences
    delete_stmt = delete(UserTeamPreference).where(UserTeamPreference.user_id == user_id)
    db.execute(delete_stmt)
    
    # Add new preferences
    new_preferences = []
    for pref in preferences:
        new_pref = UserTeamPreference(
            user_id=user_id,
            team_id=pref.team_id,
            interest_level=pref.interest_level
        )
        db.add(new_pref)
        new_preferences.append(new_pref)
    
    db.commit()
    
    # Refresh to get relationships loaded
    for pref in new_preferences:
        db.refresh(pref)
    
    response_data = [map_user_team_preference_to_response(pref) for pref in new_preferences]
    return ApiResponse.success(data=response_data)

@router.get("/preferences", response_model=ApiResponse[dict])
@require_auth
async def get_user_preferences(
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get user's current sport and team preferences with optimized query."""
    
    # Optimized query using CTEs and explicit joins
    query = text("""
        WITH sport_prefs AS (
            SELECT 
                usp.id,
                usp.user_id,
                usp.sport_id,
                s.name as sport_name,
                usp.interest_level,
                usp.created_at
            FROM user_sport_preferences usp
            JOIN sports s ON usp.sport_id = s.id
            WHERE usp.user_id = :user_id AND s.is_active = true
            ORDER BY usp.created_at DESC
        ),
        team_prefs AS (
            SELECT 
                utp.id,
                utp.user_id,
                utp.team_id,
                t.name as team_name,
                s.name as sport_name,
                utp.interest_level,
                utp.created_at
            FROM user_team_preferences utp
            JOIN teams t ON utp.team_id = t.id
            JOIN sports s ON t.sport_id = s.id
            WHERE utp.user_id = :user_id AND t.is_active = true AND s.is_active = true
            ORDER BY utp.created_at DESC
        )
        SELECT 
            'sport' as pref_type,
            sp.id,
            sp.user_id,
            sp.sport_id as entity_id,
            NULL as team_id,
            sp.sport_name as entity_name,
            NULL as sport_name,
            sp.interest_level,
            sp.created_at
        FROM sport_prefs sp
        UNION ALL
        SELECT 
            'team' as pref_type,
            tp.id,
            tp.user_id,
            tp.team_id as entity_id,
            tp.team_id,
            tp.team_name as entity_name,
            tp.sport_name,
            tp.interest_level,
            tp.created_at
        FROM team_prefs tp
        ORDER BY created_at DESC
    """)
    
    results = db.execute(query, {"user_id": user_id}).fetchall()
    
    sport_preferences = []
    team_preferences = []
    
    for row in results:
        if row.pref_type == 'sport':
            sport_preferences.append({
                "id": row.id,
                "user_id": row.user_id,
                "sport_id": row.entity_id,
                "sport_name": row.entity_name,
                "interest_level": row.interest_level,
                "created_at": row.created_at.isoformat() if row.created_at else None
            })
        elif row.pref_type == 'team':
            team_preferences.append({
                "id": row.id,
                "user_id": row.user_id,
                "team_id": row.entity_id,
                "team_name": row.entity_name,
                "sport_name": row.sport_name,
                "interest_level": row.interest_level,
                "created_at": row.created_at.isoformat() if row.created_at else None
            })
    
    response_data = {
        "sport_preferences": sport_preferences,
        "team_preferences": team_preferences
    }
    
    return ApiResponse.success(data=response_data)
