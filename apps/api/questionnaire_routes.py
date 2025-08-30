
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from libs.api.mappers import (
    map_sport_to_response,
    map_team_to_response,
    map_user_sport_preference_to_response,
    map_user_team_preference_to_response,
)
from libs.api.response import ApiResponse
from libs.auth.decorators import require_auth
from libs.common.database import get_db
from libs.common.questionnaire_models import Sport, Team, UserSportPreference, UserTeamPreference

router = APIRouter()

# Response Models
class SportResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: str | None
    is_active: bool

class TeamResponse(BaseModel):
    id: int
    name: str
    display_name: str
    sport_id: int
    sport_name: str | None
    city: str | None
    state: str | None
    country: str | None
    league: str | None
    is_active: bool

class UserSportPreferenceResponse(BaseModel):
    id: int
    user_id: str
    sport_id: int
    sport_name: str | None
    interest_level: int
    created_at: str | None

class UserTeamPreferenceResponse(BaseModel):
    id: int
    user_id: str
    team_id: int
    team_name: str | None
    sport_name: str | None
    interest_level: int
    created_at: str | None

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

class SportRankingRequest(BaseModel):
    sport_rankings: list[str]

@router.get("/status", response_model=ApiResponse[QuestionnaireStatusResponse])
async def get_questionnaire_status(
    credentials: HTTPAuthorizationCredentials = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Get questionnaire completion status for the current user with optimized query."""

    user_id = credentials.user_id

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

    result = await db.execute(query, {"user_id": user_id})
    row = result.fetchone()

    if not row:
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
            sports_completed=bool(row.sports_completed),
            teams_completed=bool(row.teams_completed),
            total_sports_selected=row.sport_count or 0,
            total_teams_selected=row.team_count or 0,
            completion_percentage=float(row.completion_percentage or 0.0)
        )

    return ApiResponse(success=True, data=response_data)

@router.get("/sports", response_model=ApiResponse[list[SportResponse]])
async def get_available_sports(db: AsyncSession = Depends(get_db)):
    """Get all available sports."""

    # Use explicit select with where clause
    stmt = select(Sport).where(Sport.is_active == True).order_by(Sport.display_name)
    result = await db.execute(stmt)
    sports = result.scalars().all()

    response_data = [map_sport_to_response(sport) for sport in sports]
    return ApiResponse(success=True, data=response_data)

@router.get("/teams", response_model=ApiResponse[list[TeamResponse]])
async def get_teams_by_sport(
    sport_id: int = Query(..., description="Sport ID to filter teams"),
    db: AsyncSession = Depends(get_db)
):
    """Get teams for a specific sport."""

    # Verify sport exists and is active
    sport_stmt = select(Sport).where(Sport.id == sport_id, Sport.is_active == True)
    result = await db.execute(sport_stmt)
    sport = result.scalar_one_or_none()

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
    result = await db.execute(teams_stmt)
    teams = result.scalars().all()

    response_data = [map_team_to_response(team) for team in teams]
    return ApiResponse(success=True, data=response_data)

@router.get("/sports/{sport_id}/teams", response_model=ApiResponse[list[TeamResponse]])
async def get_teams_by_sport_path(
    sport_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get teams for a specific sport (path parameter version)."""

    # Verify sport exists and is active
    sport_stmt = select(Sport).where(Sport.id == sport_id, Sport.is_active == True)
    result = await db.execute(sport_stmt)
    sport = result.scalar_one_or_none()

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
    result = await db.execute(teams_stmt)
    teams = result.scalars().all()

    response_data = [map_team_to_response(team) for team in teams]
    return ApiResponse(success=True, data=response_data)

@router.post(
    "/sports/preferences",
    response_model=ApiResponse[list[UserSportPreferenceResponse]],
)
async def save_sport_preferences(
    preferences: list[SportPreferenceRequest],
    credentials: HTTPAuthorizationCredentials = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Save user sport preferences."""

    user_id = credentials.user_id
    print(f"DEBUG: Function called with user_id: {user_id}")
    print(f"DEBUG: Raw preferences type: {type(preferences)}")
    print(f"DEBUG: Raw preferences: {preferences}")
    print(f"DEBUG: Preferences length: {len(preferences) if preferences else 'None'}")

    if preferences:
        for i, pref in enumerate(preferences):
            print(f"DEBUG: Preference {i}: sport_id={pref.sport_id} (type: {type(pref.sport_id)}), interest_level={pref.interest_level} (type: {type(pref.interest_level)})")

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
    result = await db.execute(sports_stmt)
    existing_sports = result.scalars().all()
    existing_sport_ids = {sport.id for sport in existing_sports}

    invalid_sport_ids = set(sport_ids) - existing_sport_ids
    if invalid_sport_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or inactive sport IDs: {list(invalid_sport_ids)}"
        )

    # Delete existing preferences
    delete_stmt = delete(UserSportPreference).where(UserSportPreference.user_id == user_id)
    await db.execute(delete_stmt)

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

    await db.commit()

    # Refresh to get relationships loaded
    for pref in new_preferences:
        await db.refresh(pref)

    response_data = [map_user_sport_preference_to_response(pref) for pref in new_preferences]
    return ApiResponse(success=True, data=response_data)

@router.post(
    "/sports/ranking",
    response_model=ApiResponse[list[str]],
)
async def save_sport_rankings(
    request: SportRankingRequest,
    credentials: HTTPAuthorizationCredentials = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Save user sport rankings (preference order)."""

    user_id = credentials.user_id
    sport_rankings = request.sport_rankings

    # Validate that all sport IDs are valid integers and exist
    try:
        sport_ids = [int(sport_id) for sport_id in sport_rankings]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All sport rankings must be valid integer IDs"
        )

    # Verify all sports exist and are active
    sports_stmt = select(Sport).where(Sport.id.in_(sport_ids), Sport.is_active == True)
    result = await db.execute(sports_stmt)
    existing_sports = result.scalars().all()
    existing_sport_ids = {sport.id for sport in existing_sports}

    invalid_sport_ids = set(sport_ids) - existing_sport_ids
    if invalid_sport_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or inactive sport IDs: {list(invalid_sport_ids)}"
        )

    # Update the preference_order for existing sport preferences
    for order, sport_id in enumerate(sport_ids, 1):
        # Update existing preference with new order
        update_stmt = (
            select(UserSportPreference)
            .where(
                UserSportPreference.user_id == user_id,
                UserSportPreference.sport_id == sport_id
            )
        )
        result = await db.execute(update_stmt)
        preference = result.scalar_one_or_none()

        if preference:
            preference.preference_order = order
        else:
            # Create new preference if it doesn't exist (with default interest level)
            new_preference = UserSportPreference(
                user_id=user_id,
                sport_id=sport_id,
                interest_level=3,  # Default moderate interest
                preference_order=order
            )
            db.add(new_preference)

    await db.commit()

    # Return the updated rankings
    return ApiResponse(success=True, data=sport_rankings)


@router.put(
    "/sports/ranking",
    response_model=ApiResponse[list[str]],
)
async def update_sport_ranking(
    request: SportRankingRequest,
    credentials: HTTPAuthorizationCredentials = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Alias for ``save_sport_rankings`` using HTTP PUT."""

    return await save_sport_rankings(request, credentials, db)

@router.post(
    "/teams/preferences",
    response_model=ApiResponse[list[UserTeamPreferenceResponse]],
)
async def save_team_preferences(
    preferences: list[TeamPreferenceRequest],
    credentials: HTTPAuthorizationCredentials = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Save user team preferences."""

    user_id = credentials.user_id

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
    result = await db.execute(teams_stmt)
    existing_teams = result.scalars().all()
    existing_team_ids = {team.id for team in existing_teams}

    invalid_team_ids = set(team_ids) - existing_team_ids
    if invalid_team_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or inactive team IDs: {list(invalid_team_ids)}"
        )

    # Delete existing preferences
    delete_stmt = delete(UserTeamPreference).where(UserTeamPreference.user_id == user_id)
    await db.execute(delete_stmt)

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

    await db.commit()

    # Refresh to get relationships loaded
    for pref in new_preferences:
        await db.refresh(pref)

    response_data = [map_user_team_preference_to_response(pref) for pref in new_preferences]
    return ApiResponse(success=True, data=response_data)

@router.get("/preferences", response_model=ApiResponse[dict])
async def get_user_preferences(
    credentials: HTTPAuthorizationCredentials = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Get user's current sport and team preferences with optimized query."""

    user_id = credentials.user_id

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

    result = await db.execute(query, {"user_id": user_id})
    results = result.fetchall()

    sport_preferences = []
    team_preferences = []

    for row in results:
        if row.pref_type == "sport":
            sport_preferences.append({
                "id": row.id,
                "user_id": row.user_id,
                "sport_id": row.entity_id,
                "sport_name": row.entity_name,
                "interest_level": row.interest_level,
                "created_at": row.created_at.isoformat() if row.created_at else None
            })
        elif row.pref_type == "team":
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

    return ApiResponse(success=True, data=response_data)
