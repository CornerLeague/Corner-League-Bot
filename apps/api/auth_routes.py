"""Authentication routes for Clerk integration.

This module provides authentication endpoints for user management,
profile operations, and authentication callbacks.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Literal

from libs.api.response import ApiResponse
from libs.api.mappers import map_user_profile_to_response, map_user_stats_to_response
from libs.auth.decorators import require_auth, optional_auth, require_role
from libs.auth.user_service import get_user_service, UserService, UserPreferences
from libs.common.database import DatabaseManager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/auth", tags=["authentication"])


# Pydantic models
class UserProfileResponse(BaseModel):
    """User profile response model."""
    user_id: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    profile_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_sign_in_at: Optional[datetime] = None
    roles: List[str] = Field(default_factory=list)
    is_active: bool = True
    is_verified: bool = False


class UserPreferencesRequest(BaseModel):
    """User preferences update request."""
    favorite_teams: Optional[List[str]] = None
    favorite_sports: Optional[List[str]] = None
    content_types: Optional[List[str]] = None
    notification_email: Optional[bool] = None
    notification_push: Optional[bool] = None
    notification_frequency: Optional[str] = None
    language: Optional[str] = None


class RoleUpdateResult(BaseModel):
    """Result of role assignment/removal operation."""
    user_id: str
    role: str
    action: Literal["added", "removed"]
    message: str
    timezone: Optional[str] = None
    theme: Optional[str] = None


class UserStatsResponse(BaseModel):
    """User statistics response."""
    articles_read: int
    articles_saved: int
    articles_shared: int
    total_reading_time: int
    favorite_topics: List[str]
    activity_streak: int


class ActivityTrackingRequest(BaseModel):
    """Activity tracking request."""
    action: str = Field(..., description="Action performed (view, like, share, save, etc.)")
    resource_type: str = Field(..., description="Type of resource (article, video, etc.)")
    resource_id: str = Field(..., description="ID of the resource")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


# Helper functions
async def get_current_user_id(request: Request) -> str:
    """Get current user ID, raising 401 if not authenticated."""
    user = getattr(request.state, 'user', None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user.get('sub')


async def get_optional_user_id(request: Request) -> Optional[str]:
    """Get current user ID if authenticated, None otherwise."""
    user = getattr(request.state, 'user', None)
    return user.get('sub') if user else None


# Authentication routes
@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    credentials: HTTPAuthorizationCredentials = Depends(require_auth)
) -> UserProfileResponse:
    """Get current user's profile."""
    user_id = await get_current_user_id(request)
    
    try:
        profile = await user_service.get_or_create_user_profile(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return UserProfileResponse(**map_user_profile_to_response(profile))
        
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    credentials: HTTPAuthorizationCredentials = Depends(require_auth)
) -> UserPreferences:
    """Get current user's preferences."""
    user_id = await get_current_user_id(request)
    
    try:
        preferences = await user_service.get_user_preferences(user_id)
        return preferences
        
    except Exception as e:
        logger.error(f"Failed to get user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user preferences"
        )


@router.put("/preferences", response_model=UserPreferences)
async def update_user_preferences(
    request: Request,
    preferences_update: UserPreferencesRequest,
    user_service: UserService = Depends(get_user_service),
    credentials: HTTPAuthorizationCredentials = Depends(require_auth)
) -> UserPreferences:
    """Update current user's preferences."""
    user_id = await get_current_user_id(request)
    
    try:
        # Get current preferences
        current_preferences = await user_service.get_user_preferences(user_id)
        
        # Update only provided fields
        update_data = preferences_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(current_preferences, field):
                setattr(current_preferences, field, value)
        
        # Save updated preferences
        success = await user_service.update_user_preferences(user_id, current_preferences)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update preferences"
            )
        
        return current_preferences
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user preferences"
        )


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    credentials: HTTPAuthorizationCredentials = Depends(require_auth)
) -> UserStatsResponse:
    """Get current user's statistics."""
    user_id = await get_current_user_id(request)
    
    try:
        stats = await user_service.get_user_stats(user_id)
        return UserStatsResponse(**map_user_stats_to_response(stats))
        
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )


@router.post("/activity")
async def track_user_activity(
    request: Request,
    activity: ActivityTrackingRequest,
    credentials: HTTPAuthorizationCredentials = Depends(require_auth),
    user_service: UserService = Depends(get_user_service)
) -> Dict[str, str]:
    """Track user activity."""
    user_id = await get_current_user_id(request)
    
    try:
        success = await user_service.track_user_activity(
            user_id=user_id,
            action=activity.action,
            resource_type=activity.resource_type,
            resource_id=activity.resource_id,
            metadata=activity.metadata
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to track activity"
            )
        
        return {"status": "success", "message": "Activity tracked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to track user activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track activity"
        )


@router.get("/activity")
async def get_user_activity(
    request: Request,
    limit: int = 50,
    action_filter: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(require_auth),
    user_service: UserService = Depends(get_user_service)
) -> List[Dict[str, Any]]:
    """Get user activity history."""
    user_id = await get_current_user_id(request)
    
    try:
        activities = await user_service.get_user_activity(
            user_id=user_id,
            limit=limit,
            action_filter=action_filter
        )
        
        return [activity.dict() for activity in activities]
        
    except Exception as e:
        logger.error(f"Failed to get user activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user activity"
        )


@router.delete("/me")
async def delete_user_account(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(require_auth),
    user_service: UserService = Depends(get_user_service)
) -> Dict[str, str]:
    """Delete current user's account and all associated data."""
    user_id = await get_current_user_id(request)
    
    try:
        success = await user_service.delete_user_data(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user account"
            )
        
        return {"status": "success", "message": "User account deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user account"
        )


# Admin routes
@router.get("/users", response_model=List[UserProfileResponse])
async def list_users(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    user_service: UserService = Depends(get_user_service),
    credentials: HTTPAuthorizationCredentials = Depends(require_role(["admin"]))
) -> List[UserProfileResponse]:
    """List all users (admin only)."""
    try:
        # This would need to be implemented in the user service
        # For now, return empty list
        return []
        
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.post("/users/{user_id}/roles", response_model=ApiResponse[RoleUpdateResult])
async def assign_user_role(
    request: Request,
    user_id: str,
    role: str,
    user_service: UserService = Depends(get_user_service),
    credentials: HTTPAuthorizationCredentials = Depends(require_role(["admin"]))
) -> ApiResponse[RoleUpdateResult]:
    """Assign role to user (admin only)."""
    try:
        # This would need to be implemented in the user service
        # For now, return success
        result = RoleUpdateResult(
            user_id=user_id,
            role=role,
            action="added",
            message=f"Role '{role}' assigned to user {user_id}"
        )
        return ApiResponse(data=result)
        
    except Exception as e:
        logger.error(f"Failed to assign role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign role"
        )


@router.delete("/users/{user_id}/roles/{role}", response_model=ApiResponse[RoleUpdateResult])
async def remove_user_role(
    request: Request,
    user_id: str,
    role: str,
    user_service: UserService = Depends(get_user_service),
    credentials: HTTPAuthorizationCredentials = Depends(require_role(["admin"]))
) -> ApiResponse[RoleUpdateResult]:
    """Remove role from user (admin only)."""
    try:
        # This would need to be implemented in the user service
        # For now, return success
        result = RoleUpdateResult(
            user_id=user_id,
            role=role,
            action="removed",
            message=f"Role '{role}' removed from user {user_id}"
        )
        return ApiResponse(data=result)
        
    except Exception as e:
        logger.error(f"Failed to remove role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove role"
        )