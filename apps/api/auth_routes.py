from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from typing import List
from pydantic import BaseModel

from libs.auth.decorators import require_auth, require_admin
from libs.auth.user_service import UserService
from libs.api.response import ApiResponse
from libs.api.mappers import map_user_profile_to_response

router = APIRouter()

# Response Models
class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    first_name: str
    last_name: str
    roles: List[str]
    created_at: str
    updated_at: str

class RoleAssignmentResponse(BaseModel):
    user_id: str
    role: str
    assigned: bool
    message: str

class RoleRemovalResponse(BaseModel):
    user_id: str
    role: str
    removed: bool
    message: str

# Request Models
class RoleAssignmentRequest(BaseModel):
    user_id: str
    role: str

class RoleRemovalRequest(BaseModel):
    user_id: str
    role: str

@router.get("/profile", response_model=ApiResponse[UserProfileResponse])
async def get_user_profile(
    credentials: HTTPAuthorizationCredentials = Depends(require_auth)
):
    """Get the current user's profile."""
    user_id = credentials.user_id
    user_service = UserService()
    profile = await user_service.get_user_profile(user_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    response_data = map_user_profile_to_response(profile)
    return ApiResponse.success(data=response_data)

@router.post(
    "/assign-role",
    response_model=ApiResponse[RoleAssignmentResponse],
    dependencies=[Depends(require_admin)],
)
async def assign_user_role(
    request: RoleAssignmentRequest,
):
    """Assign a role to a user (admin only)."""
    user_service = UserService()
    
    try:
        success = await user_service.assign_role(request.user_id, request.role)
        
        if success:
            response_data = RoleAssignmentResponse(
                user_id=request.user_id,
                role=request.role,
                assigned=True,
                message=f"Role '{request.role}' successfully assigned to user {request.user_id}"
            )
            return ApiResponse.success(data=response_data)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to assign role '{request.role}' to user {request.user_id}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning role: {str(e)}"
        )

@router.post(
    "/remove-role",
    response_model=ApiResponse[RoleRemovalResponse],
    dependencies=[Depends(require_admin)],
)
async def remove_user_role(
    request: RoleRemovalRequest,
):
    """Remove a role from a user (admin only)."""
    user_service = UserService()
    
    try:
        success = await user_service.remove_role(request.user_id, request.role)
        
        if success:
            response_data = RoleRemovalResponse(
                user_id=request.user_id,
                role=request.role,
                removed=True,
                message=f"Role '{request.role}' successfully removed from user {request.user_id}"
            )
            return ApiResponse.success(data=response_data)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to remove role '{request.role}' from user {request.user_id}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing role: {str(e)}"
        )

@router.get(
    "/users",
    response_model=ApiResponse[List[UserProfileResponse]],
    dependencies=[Depends(require_admin)],
)
async def list_users():
    """List all users (admin only)."""
    user_service = UserService()
    users = await user_service.list_users()
    
    response_data = [map_user_profile_to_response(user) for user in users]
    return ApiResponse.success(data=response_data)
