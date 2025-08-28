"""Authentication and authorization module for Corner League Bot.

This module provides Clerk-based authentication and authorization functionality
including JWT token validation, user management, and role-based access control.
"""

from .clerk_config import ClerkConfig, get_clerk_config
from .middleware import ClerkAuthMiddleware
from .decorators import require_auth, require_admin, require_role
from .user_service import UserService, get_user_service

__all__ = [
    "ClerkConfig",
    "get_clerk_config",
    "ClerkAuthMiddleware", 
    "require_auth",
    "require_admin",
    "require_role",
    "UserService",
    "get_user_service",
]