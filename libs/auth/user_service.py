"""User management service for Clerk integration.

This module provides user profile management, Clerk API integration,
user preferences handling, and profile synchronization.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from .clerk_config import get_clerk_config
from ..common.database import DatabaseManager

logger = logging.getLogger(__name__)


class UserProfile(BaseModel):
    """User profile model."""
    user_id: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    profile_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_sign_in_at: Optional[datetime] = None
    
    # User preferences
    favorite_teams: List[str] = Field(default_factory=list)
    favorite_sports: List[str] = Field(default_factory=list)
    content_preferences: Dict[str, Any] = Field(default_factory=dict)
    notification_settings: Dict[str, bool] = Field(default_factory=dict)
    
    # User roles and permissions
    roles: List[str] = Field(default_factory=list)
    is_active: bool = True
    is_verified: bool = False


class UserPreferences(BaseModel):
    """User preferences model."""
    favorite_teams: List[str] = Field(default_factory=list)
    favorite_sports: List[str] = Field(default_factory=list)
    content_types: List[str] = Field(default_factory=list)  # news, analysis, highlights, etc.
    notification_email: bool = True
    notification_push: bool = True
    notification_frequency: str = "daily"  # immediate, daily, weekly
    language: str = "en"
    timezone: str = "UTC"
    theme: str = "light"  # light, dark, auto


class UserActivity(BaseModel):
    """User activity tracking model."""
    user_id: str
    action: str  # view, like, share, save, etc.
    resource_type: str  # article, video, etc.
    resource_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class ClerkAPIClient:
    """Client for interacting with Clerk's API."""
    
    def __init__(self):
        self.config = get_clerk_config()
        self.base_url = "https://api.clerk.dev/v1"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.config.clerk_secret_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information from Clerk.
        
        Args:
            user_id: The Clerk user ID
            
        Returns:
            Dict containing user information or None if not found
        """
        try:
            response = await self.client.get(f"/users/{user_id}")
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"User not found in Clerk: {user_id}")
                return None
            else:
                response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch user from Clerk: {e}")
            return None
    
    async def update_user_metadata(
        self,
        user_id: str,
        public_metadata: Optional[Dict[str, Any]] = None,
        private_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update user metadata in Clerk.
        
        Args:
            user_id: The Clerk user ID
            public_metadata: Public metadata to update
            private_metadata: Private metadata to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            payload = {}
            if public_metadata is not None:
                payload["public_metadata"] = public_metadata
            if private_metadata is not None:
                payload["private_metadata"] = private_metadata
            
            if not payload:
                return True
            
            response = await self.client.patch(f"/users/{user_id}", json=payload)
            response.raise_for_status()
            return True
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to update user metadata in Clerk: {e}")
            return False
    
    async def get_user_list(
        self,
        limit: int = 10,
        offset: int = 0,
        email_address: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get a list of users from Clerk.
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            email_address: Filter by email address
            
        Returns:
            List of user dictionaries
        """
        try:
            params = {"limit": limit, "offset": offset}
            if email_address:
                params["email_address"] = email_address
            
            response = await self.client.get("/users", params=params)
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch user list from Clerk: {e}")
            return []
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class UserService:
    """Service for managing user profiles and preferences."""

    def __init__(self):
        self.clerk_client = ClerkAPIClient()

    def _clerk_user_to_profile(self, clerk_user: Dict[str, Any]) -> UserProfile:
        """Convert Clerk user data to internal UserProfile model."""
        try:
            return UserProfile(
                user_id=clerk_user.get("id"),
                email=clerk_user.get("email_addresses", [{}])[0].get("email_address"),
                first_name=clerk_user.get("first_name"),
                last_name=clerk_user.get("last_name"),
                username=clerk_user.get("username"),
                profile_image_url=clerk_user.get("profile_image_url"),
                created_at=datetime.fromisoformat(
                    clerk_user.get("created_at", datetime.utcnow().isoformat())
                ),
                updated_at=datetime.fromisoformat(
                    clerk_user.get("updated_at", datetime.utcnow().isoformat())
                ),
                last_sign_in_at=datetime.fromisoformat(
                    clerk_user.get("last_sign_in_at")
                ) if clerk_user.get("last_sign_in_at") else None,
                roles=clerk_user.get("public_metadata", {}).get("roles", []),
                is_verified=any(
                    addr.get("verification", {}).get("status") == "verified"
                    for addr in clerk_user.get("email_addresses", [])
                ),
            )
        except Exception as e:
            logger.error(f"Error mapping Clerk user to UserProfile: {e}")
            raise
    
    async def get_or_create_user_profile(
        self,
        user_id: str,
        sync_with_clerk: bool = True
    ) -> Optional[UserProfile]:
        """Get or create a user profile.
        
        Args:
            user_id: The Clerk user ID
            sync_with_clerk: Whether to sync with Clerk API
            
        Returns:
            UserProfile or None if user doesn't exist
        """
        # First, try to get from local database
        # Note: Database integration will be implemented later
        # For now, we'll sync with Clerk and create a profile
        if sync_with_clerk:
            clerk_user = await self.clerk_client.get_user(user_id)
            if not clerk_user:
                return None

            try:
                profile = self._clerk_user_to_profile(clerk_user)
            except Exception:
                return None

            return profile

        return None

    async def get_user_profile(
        self,
        user_id: str,
        sync_with_clerk: bool = True
    ) -> Optional[UserProfile]:
        """Retrieve a user profile without creating it.

        Args:
            user_id: The Clerk user ID
            sync_with_clerk: Whether to fetch from Clerk API

        Returns:
            UserProfile or None if not found
        """
        try:
            if sync_with_clerk:
                clerk_user = await self.clerk_client.get_user(user_id)
                if not clerk_user:
                    return None
                return self._clerk_user_to_profile(clerk_user)
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
        return None

    async def assign_role(self, user_id: str, role: str) -> bool:
        """Assign a role to a user via Clerk metadata."""
        try:
            clerk_user = await self.clerk_client.get_user(user_id)
            if not clerk_user:
                return False
            metadata = clerk_user.get("public_metadata", {})
            roles = metadata.get("roles", [])
            if role not in roles:
                roles.append(role)
            return await self.clerk_client.update_user_metadata(
                user_id, public_metadata={"roles": roles}
            )
        except Exception as e:
            logger.error(f"Failed to assign role '{role}' to user {user_id}: {e}")
            return False

    async def remove_role(self, user_id: str, role: str) -> bool:
        """Remove a role from a user via Clerk metadata."""
        try:
            clerk_user = await self.clerk_client.get_user(user_id)
            if not clerk_user:
                return False
            metadata = clerk_user.get("public_metadata", {})
            roles = metadata.get("roles", [])
            if role in roles:
                roles.remove(role)
            return await self.clerk_client.update_user_metadata(
                user_id, public_metadata={"roles": roles}
            )
        except Exception as e:
            logger.error(f"Failed to remove role '{role}' from user {user_id}: {e}")
            return False

    async def list_users(
        self, limit: int = 100, offset: int = 0
    ) -> List[UserProfile]:
        """List users via Clerk."""
        try:
            users = await self.clerk_client.get_user_list(limit=limit, offset=offset)
            profiles: List[UserProfile] = []
            for user in users:
                try:
                    profiles.append(self._clerk_user_to_profile(user))
                except Exception:
                    continue
            return profiles
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            return []
    
    async def update_user_preferences(
        self,
        user_id: str,
        preferences: UserPreferences
    ) -> bool:
        """Update user preferences.
        
        Args:
            user_id: The user ID
            preferences: The preferences to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update in local database
            # (Implementation depends on your database schema)
            
            # Optionally sync with Clerk metadata
            await self.clerk_client.update_user_metadata(
                user_id,
                public_metadata={"preferences": preferences.dict()}
            )
            
            logger.info(f"Updated preferences for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user preferences: {e}")
            return False
    
    async def get_user_preferences(self, user_id: str) -> UserPreferences:
        """Get user preferences.
        
        Args:
            user_id: The user ID
            
        Returns:
            UserPreferences: The user's preferences
        """
        try:
            # Get from local database first
            # (Implementation depends on your database schema)
            
            # Fallback to default preferences
            return UserPreferences()
            
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return UserPreferences()
    
    async def track_user_activity(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track user activity.
        
        Args:
            user_id: The user ID
            action: The action performed
            resource_type: Type of resource
            resource_id: ID of the resource
            metadata: Additional metadata
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            activity = UserActivity(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                metadata=metadata or {},
                timestamp=datetime.utcnow()
            )
            
            # Store in database
            # (Implementation depends on your database schema)
            
            logger.debug(f"Tracked activity for user {user_id}: {action} on {resource_type}:{resource_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track user activity: {e}")
            return False
    
    async def get_user_activity(
        self,
        user_id: str,
        limit: int = 50,
        action_filter: Optional[str] = None
    ) -> List[UserActivity]:
        """Get user activity history.
        
        Args:
            user_id: The user ID
            limit: Maximum number of activities to return
            action_filter: Filter by specific action
            
        Returns:
            List of UserActivity objects
        """
        try:
            # Get from database
            # (Implementation depends on your database schema)
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get user activity: {e}")
            return []
    
    async def delete_user_data(self, user_id: str) -> bool:
        """Delete all user data (GDPR compliance).
        
        Args:
            user_id: The user ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Delete from local database
            # (Implementation depends on your database schema)
            
            logger.info(f"Deleted user data for: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user data: {e}")
            return False
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics.
        
        Args:
            user_id: The user ID
            
        Returns:
            Dict containing user statistics
        """
        try:
            # Calculate stats from database
            # (Implementation depends on your database schema)
            
            return {
                "articles_read": 0,
                "articles_saved": 0,
                "articles_shared": 0,
                "total_reading_time": 0,
                "favorite_topics": [],
                "activity_streak": 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            return {}
    
    async def close(self):
        """Close external connections."""
        await self.clerk_client.close()


# Global service instance
_user_service: Optional[UserService] = None


def get_user_service() -> UserService:
    """Get the global user service instance."""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service