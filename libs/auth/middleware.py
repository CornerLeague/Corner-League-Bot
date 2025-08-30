"""Clerk authentication middleware for FastAPI.

This module provides middleware for JWT token validation, user context injection,
and request state management using Clerk authentication.
"""

import logging
from typing import Optional, Dict, Any, Callable, List
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import jwt
import httpx
import asyncio
from datetime import datetime, timedelta
from functools import lru_cache
from pydantic import BaseModel

from .clerk_config import get_clerk_config

logger = logging.getLogger(__name__)


class EnhancedCredentials(BaseModel):
    """Enhanced credentials with decoded JWT payload"""
    scheme: str
    credentials: str
    decoded: Dict[str, Any]
    user_id: str
    user_email: Optional[str] = None
    user_roles: List[str] = []


class JWKSCache:
    """Cache for JWKS (JSON Web Key Set) to avoid frequent API calls."""
    
    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
    
    def get(self, url: str) -> Optional[Dict[str, Any]]:
        """Get JWKS from cache if not expired."""
        if url not in self._cache:
            return None
        
        timestamp = self._timestamps.get(url)
        if not timestamp:
            return None
        
        if datetime.utcnow() - timestamp > timedelta(seconds=self.ttl_seconds):
            # Cache expired
            del self._cache[url]
            del self._timestamps[url]
            return None
        
        return self._cache[url]
    
    def set(self, url: str, jwks: Dict[str, Any]):
        """Set JWKS in cache with current timestamp."""
        self._cache[url] = jwks
        self._timestamps[url] = datetime.utcnow()
    
    def _lock_for(self, url: str) -> asyncio.Lock:
        if url not in self._locks:
            self._locks[url] = asyncio.Lock()
        return self._locks[url]

    async def get_or_fetch(
        self,
        url: str,
        fetch_fn: Callable[[str], Any],
    ) -> Dict[str, Any]:
        cached = self.get(url)
        if cached:
            return cached
        lock = self._lock_for(url)
        async with lock:
            cached = self.get(url)
            if cached:
                return cached
            fresh = await fetch_fn(url)
            self.set(url, fresh)
            return fresh
    
    def clear(self):
        """Clear the entire cache."""
        self._cache.clear()
        self._timestamps.clear()


class ClerkTokenValidator:
    """Validates Clerk JWT tokens using JWKS."""
    
    def __init__(self):
        self.config = get_clerk_config()
        self.jwks_cache = JWKSCache(ttl_seconds=self.config.jwks_cache_ttl)
        self.http_client = httpx.AsyncClient(
            timeout=self.config.request_timeout,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
    
    async def _fetch_jwks(self, jwks_url: str) -> Dict[str, Any]:
        """Fetch JWKS from Clerk's endpoint with caching and concurrency safety."""
        async def _do_fetch(url: str) -> Dict[str, Any]:
            try:
                logger.debug(f"Fetching JWKS from {url}")
                response = await self.http_client.get(url)
                response.raise_for_status()
                jwks = response.json()
                logger.debug("JWKS fetched successfully")
                return jwks
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch JWKS: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service temporarily unavailable"
                )
        
        return await self.jwks_cache.get_or_fetch(jwks_url, _do_fetch)
    
    def _get_signing_key(self, jwks: Dict[str, Any], kid: str) -> str:
        """Extract the signing key from JWKS for the given key ID."""
        keys = jwks.get('keys', [])
        
        for key in keys:
            if key.get('kid') == kid:
                # Convert JWK to PEM format for PyJWT
                try:
                    from jwt.algorithms import RSAAlgorithm
                    return RSAAlgorithm.from_jwk(key)
                except Exception as e:
                    logger.error(f"Failed to convert JWK to PEM: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token signature"
                    )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token signing key not found"
        )
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate a Clerk JWT token and return the decoded payload.
        
        Args:
            token: The JWT token to validate
            
        Returns:
            Dict containing the decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Decode header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
            
            if not kid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing key ID"
                )
            
            # Fetch JWKS and get signing key
            jwks_url = self.config.get_jwks_url()
            jwks = await self._fetch_jwks(jwks_url)
            signing_key = self._get_signing_key(jwks, kid)
            
            # Validate and decode token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=self.config.jwt_algorithms,
                issuer=self.config.get_issuer(),
                # Temporarily disable audience validation
                # audience=self.config.jwt_audience,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_iss": True,
                    "require_exp": True,
                    "require_iat": True,
                    "verify_aud": False,  # Disable audience verification
                }
            )
            
            logger.debug(f"Token validated successfully for user: {payload.get('sub')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication error"
            )
    
    async def close(self):
        """Close the HTTP client and clean up resources."""
        # Cancel any pending requests
        for task in self._pending_requests.values():
            if not task.done():
                task.cancel()
        
        # Wait for all tasks to complete or be cancelled
        if self._pending_requests:
            await asyncio.gather(*self._pending_requests.values(), return_exceptions=True)
        
        # Clear resources
        self._pending_requests.clear()
        self._jwks_locks.clear()
        
        await self.http_client.aclose()


class ClerkAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to handle Clerk authentication for all requests.
    
    This middleware automatically validates JWT tokens and injects user context
    into the request state for protected routes.
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.validator = ClerkTokenValidator()
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/health",
            "/favicon.ico"
        ]
    
    def _should_exclude_path(self, path: str) -> bool:
        """Check if the path should be excluded from authentication."""
        return any(path.startswith(excluded) for excluded in self.exclude_paths)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and handle authentication."""
        # Skip authentication for excluded paths
        if self._should_exclude_path(request.url.path):
            return await call_next(request)
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # No token provided - continue without user context
            request.state.user = None
            request.state.authenticated = False
            return await call_next(request)
        
        token = auth_header.split(" ", 1)[1]
        
        try:
            # Validate token and set user context
            payload = await self.validator.validate_token(token)
            request.state.user = payload
            request.state.authenticated = True
            request.state.user_id = payload.get('sub')
            request.state.user_email = payload.get('email')
            request.state.user_roles = payload.get('roles', [])
            
            logger.debug(f"Authenticated request for user: {request.state.user_id}")
            
        except HTTPException:
            # Token validation failed - continue without user context
            request.state.user = None
            request.state.authenticated = False
            logger.debug("Request proceeding without authentication")
        
        return await call_next(request)


class ClerkHTTPBearer(HTTPBearer):
    """Custom HTTPBearer for Clerk authentication with automatic token validation."""
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.validator = ClerkTokenValidator()
    
    async def __call__(self, request: Request) -> Optional[EnhancedCredentials]:
        """Validate the bearer token and return credentials with decoded payload."""
        credentials = await super().__call__(request)
        
        if not credentials:
            return None
        
        try:
            # Validate token and attach decoded payload
            payload = await self.validator.validate_token(credentials.credentials)
            
            # Create enhanced credentials with decoded information
            enhanced_credentials = EnhancedCredentials(
                scheme=credentials.scheme,
                credentials=credentials.credentials,
                decoded=payload,
                user_id=payload.get('sub'),
                user_email=payload.get('email'),
                user_roles=payload.get('roles', [])
            )
            
            return enhanced_credentials
        except HTTPException as e:
            # Token validation failed - return None so require_auth can handle it properly
            logger.debug(f"Token validation failed: {e.detail}")
            return None
        except Exception as e:
            # Unexpected error during token validation
            logger.error(f"Unexpected error during token validation: {e}")
            return None


# Global instances
_clerk_bearer: Optional[ClerkHTTPBearer] = None
_token_validator: Optional[ClerkTokenValidator] = None


def get_clerk_bearer() -> ClerkHTTPBearer:
    """Get the global Clerk HTTPBearer instance."""
    global _clerk_bearer
    if _clerk_bearer is None:
        _clerk_bearer = ClerkHTTPBearer()
    return _clerk_bearer


def get_token_validator() -> ClerkTokenValidator:
    """Get the global token validator instance."""
    global _token_validator
    if _token_validator is None:
        _token_validator = ClerkTokenValidator()
    return _token_validator