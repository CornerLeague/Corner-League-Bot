"""Authentication and authorization module for Corner League Bot.

This module provides Clerk-based authentication and authorization functionality
including JWT token validation, user management, and role-based access control.
"""

from .clerk_config import ClerkConfig, get_clerk_config
from .decorators import require_admin, require_auth, require_role
from .middleware import ClerkAuthMiddleware
from .user_service import UserService, get_user_service

__all__ = [
    "ClerkAuthMiddleware",
    "ClerkConfig",
    "UserService",
    "get_clerk_config",
    "get_user_service",
    "require_admin",
    "require_auth",
    "require_role",
]
