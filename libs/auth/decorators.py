"""Authorization decorators for role-based access control.

This module provides decorators and utilities for implementing role-based
access control and permission checking in FastAPI routes.
"""

import logging
from collections.abc import Callable
from functools import wraps

from fastapi import Depends, HTTPException, Request, status

from .middleware import EnhancedCredentials, get_clerk_bearer

logger = logging.getLogger(__name__)


class PermissionError(HTTPException):
    """Custom exception for permission-related errors."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class AuthenticationError(HTTPException):
    """Custom exception for authentication-related errors."""

    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


def require_auth(
    credentials: EnhancedCredentials = Depends(get_clerk_bearer())
) -> EnhancedCredentials:
    """Dependency that requires valid authentication.

    Args:
        credentials: The enhanced credentials from Clerk with decoded JWT

    Returns:
        EnhancedCredentials: The validated credentials with user info

    Raises:
        AuthenticationError: If authentication is missing or invalid
    """
    if not credentials:
        logger.warning("Authentication required but no credentials provided")
        raise AuthenticationError("Authentication required")

    logger.debug(f"Authenticated request for user: {getattr(credentials, 'user_id', 'unknown')}")
    return credentials


def require_role(
    required_roles: list[str],
    require_all: bool = False
) -> Callable:
    """Dependency factory that requires specific user roles.

    Args:
        required_roles: List of roles that are required
        require_all: If True, user must have ALL roles. If False, user needs ANY role.

    Returns:
        Callable: A dependency function that validates roles

    Example:
        @app.get("/admin")
        async def admin_endpoint(
            user: HTTPAuthorizationCredentials = Depends(require_role(["admin"]))
        ):
            return {"message": "Admin access granted"}
    """
    def role_dependency(
        credentials: EnhancedCredentials = Depends(require_auth)
    ) -> EnhancedCredentials:
        # Skip validation if credentials is None (during module import)
        if credentials is None:
            return credentials

        user_roles = getattr(credentials, "user_roles", [])
        user_id = getattr(credentials, "user_id", "unknown")

        if require_all:
            # User must have ALL required roles
            missing_roles = set(required_roles) - set(user_roles)
            if missing_roles:
                logger.warning(
                    f"User {user_id} missing required roles: {missing_roles}"
                )
                raise PermissionError(
                    f"Missing required roles: {', '.join(missing_roles)}"
                )
        else:
            # User must have AT LEAST ONE required role
            if not any(role in user_roles for role in required_roles):
                logger.warning(
                    f"User {user_id} lacks any of required roles: {required_roles}"
                )
                raise PermissionError(
                    f"Requires one of: {', '.join(required_roles)}"
                )

        logger.debug(f"Role check passed for user {user_id} with roles: {user_roles}")
        return credentials

    return role_dependency


def require_admin(
    credentials: EnhancedCredentials = Depends(require_role(["admin"]))
) -> EnhancedCredentials:
    """Dependency that requires admin role.

    Args:
        credentials: The enhanced credentials

    Returns:
        EnhancedCredentials: The validated admin credentials

    Raises:
        PermissionError: If user is not an admin
    """
    return credentials


def require_moderator(
    credentials: EnhancedCredentials = Depends(require_role(["admin", "moderator"]))
) -> EnhancedCredentials:
    """Dependency that requires admin or moderator role.

    Args:
        credentials: The enhanced credentials

    Returns:
        EnhancedCredentials: The validated credentials

    Raises:
        PermissionError: If user is not an admin or moderator
    """
    return credentials


def optional_auth(
    request: Request
) -> dict | None:
    """Dependency that provides optional authentication.

    This dependency checks if the user is authenticated via middleware
    but doesn't require authentication. Useful for endpoints that
    behave differently for authenticated vs anonymous users.

    Args:
        request: The FastAPI request object

    Returns:
        Optional[dict]: User information if authenticated, None otherwise
    """
    if hasattr(request.state, "authenticated") and request.state.authenticated:
        return {
            "user_id": getattr(request.state, "user_id", None),
            "user_email": getattr(request.state, "user_email", None),
            "user_roles": getattr(request.state, "user_roles", []),
            "user": getattr(request.state, "user", None)
        }
    return None


def check_permission(
    user_roles: list[str],
    required_roles: list[str],
    require_all: bool = False
) -> bool:
    """Utility function to check if user has required permissions.

    Args:
        user_roles: List of roles the user has
        required_roles: List of roles that are required
        require_all: If True, user must have ALL roles. If False, user needs ANY role.

    Returns:
        bool: True if user has required permissions, False otherwise
    """
    if not required_roles:
        return True

    if require_all:
        return set(required_roles).issubset(set(user_roles))
    else:
        return any(role in user_roles for role in required_roles)


def check_resource_ownership(
    user_id: str,
    resource_owner_id: str
) -> bool:
    """Utility function to check if user owns a resource.

    Args:
        user_id: The ID of the current user
        resource_owner_id: The ID of the resource owner

    Returns:
        bool: True if user owns the resource, False otherwise
    """
    return user_id == resource_owner_id


def require_ownership_or_role(
    resource_owner_id: str,
    allowed_roles: list[str] = None
) -> Callable:
    """Dependency factory that requires resource ownership or specific roles.

    This is useful for endpoints where users can access their own resources
    or admins/moderators can access any resource.

    Args:
        resource_owner_id: The ID of the resource owner
        allowed_roles: List of roles that can bypass ownership check

    Returns:
        Callable: A dependency function that validates ownership or roles
    """
    if allowed_roles is None:
        allowed_roles = ["admin", "moderator"]

    def ownership_dependency(
        credentials: EnhancedCredentials = Depends(require_auth)
    ) -> EnhancedCredentials:
        user_id = getattr(credentials, "user_id", "")
        user_roles = getattr(credentials, "user_roles", [])

        # Check if user owns the resource
        if check_resource_ownership(user_id, resource_owner_id):
            logger.debug(f"Resource access granted to owner: {user_id}")
            return credentials

        # Check if user has required role
        if check_permission(user_roles, allowed_roles):
            logger.debug(f"Resource access granted to {user_id} with roles: {user_roles}")
            return credentials

        logger.warning(
            f"User {user_id} denied access to resource owned by {resource_owner_id}"
        )
        raise PermissionError("Access denied: insufficient permissions")

    return ownership_dependency


def rate_limit_by_user(
    max_requests: int,
    window_seconds: int = 60
) -> Callable:
    """Dependency factory for user-based rate limiting.

    Note: This is a basic implementation. For production, consider using
    Redis or a dedicated rate limiting service.

    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds

    Returns:
        Callable: A dependency function that enforces rate limits
    """
    from collections import defaultdict
    from datetime import datetime, timedelta

    # In-memory storage (use Redis in production)
    request_counts = defaultdict(list)

    def rate_limit_dependency(
        credentials: EnhancedCredentials = Depends(require_auth)
    ) -> EnhancedCredentials:
        user_id = getattr(credentials, "user_id", "")
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)

        # Clean old requests
        request_counts[user_id] = [
            timestamp for timestamp in request_counts[user_id]
            if timestamp > window_start
        ]

        # Check rate limit
        if len(request_counts[user_id]) >= max_requests:
            logger.warning(f"Rate limit exceeded for user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {max_requests} requests per {window_seconds} seconds"
            )

        # Record this request
        request_counts[user_id].append(now)

        return credentials

    return rate_limit_dependency


# Convenience decorators for common use cases
def authenticated_route(func: Callable) -> Callable:
    """Decorator to mark a route as requiring authentication.

    This is a convenience decorator that can be used instead of
    adding the Depends(require_auth) parameter.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # The actual authentication is handled by the dependency injection
        # This decorator is mainly for documentation purposes
        return await func(*args, **kwargs)

    return wrapper


def admin_only_route(func: Callable) -> Callable:
    """Decorator to mark a route as admin-only.

    This is a convenience decorator for documentation purposes.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)

    return wrapper
