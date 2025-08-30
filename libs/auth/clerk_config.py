"""Clerk authentication configuration module.

This module provides configuration management for Clerk authentication,
including environment variable validation and JWKS URL handling.
"""

import logging

from pydantic import validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class ClerkConfig(BaseSettings):
    """Configuration class for Clerk authentication settings.
    
    This class manages all Clerk-related configuration including API keys,
    JWKS URLs, and validation settings.
    """

    # Clerk API Keys
    clerk_publishable_key: str | None = None
    clerk_secret_key: str | None = None

    # Clerk URLs and endpoints
    clerk_issuer: str | None = None
    clerk_jwks_url: str | None = None

    # JWT Configuration
    jwt_algorithms: list[str] = ["RS256", "ES256", "HS256"]
    jwt_audience: str | None = None

    # Cache settings for JWKS
    jwks_cache_ttl: int = 3600  # 1 hour in seconds
    jwks_cache_max_size: int = 100

    # Request timeout settings
    request_timeout: int = 30
    max_retries: int = 3

    class Config:
        env_file = ".env"
        env_prefix = "CLERK_"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields to be ignored

    @validator("clerk_publishable_key")
    def validate_publishable_key(cls, v):
        """Validate that the publishable key has the correct format."""
        if v and not v.startswith("pk_"):
            raise ValueError("Clerk publishable key must start with 'pk_'")
        return v

    @validator("clerk_secret_key")
    def validate_secret_key(cls, v):
        """Validate that the secret key has the correct format."""
        if v and not v.startswith("sk_"):
            raise ValueError("Clerk secret key must start with 'sk_'")
        return v

    @validator("clerk_jwks_url", always=True)
    def set_jwks_url(cls, v, values):
        """Set JWKS URL based on issuer if not provided."""
        if v:
            return v

        issuer = values.get("clerk_issuer")
        if issuer:
            return f"{issuer}/.well-known/jwks.json"

        # Extract domain from publishable key for default JWKS URL
        publishable_key = values.get("clerk_publishable_key", "")
        if publishable_key.startswith("pk_test_"):
            # For test keys, use a default test domain pattern
            return "https://your-app.clerk.accounts.dev/.well-known/jwks.json"
        elif publishable_key.startswith("pk_live_"):
            # For live keys, this should be configured explicitly
            logger.warning("JWKS URL not configured for production environment")
            return None

        return None

    @validator("clerk_issuer", always=True)
    def set_issuer(cls, v, values):
        """Set issuer URL if not provided."""
        if v:
            return v

        # Extract domain from publishable key for default issuer
        publishable_key = values.get("clerk_publishable_key", "")
        if publishable_key.startswith("pk_test_"):
            return "https://your-app.clerk.accounts.dev"
        elif publishable_key.startswith("pk_live_"):
            logger.warning("Issuer URL not configured for production environment")
            return None

        return None

    def get_jwks_url(self) -> str:
        """Get the JWKS URL for token validation.
        
        Returns:
            str: The JWKS URL for fetching public keys
            
        Raises:
            ValueError: If JWKS URL is not configured
        """
        if not self.clerk_jwks_url:
            raise ValueError(
                "JWKS URL not configured. Please set CLERK_JWKS_URL or CLERK_ISSUER"
            )
        return self.clerk_jwks_url

    def get_issuer(self) -> str:
        """Get the issuer URL for token validation.
        
        Returns:
            str: The issuer URL
            
        Raises:
            ValueError: If issuer is not configured
        """
        if not self.clerk_issuer:
            raise ValueError(
                "Issuer not configured. Please set CLERK_ISSUER"
            )
        return self.clerk_issuer

    def is_production(self) -> bool:
        """Check if running in production mode.

        Returns:
            bool: True if using live keys, False otherwise.

        Safely handles missing publishable key by treating it as non-production.
        """
        key = self.clerk_publishable_key or ""
        return key.startswith("pk_live_")

    def validate_configuration(self) -> bool:
        """Validate the complete configuration.
        
        Returns:
            bool: True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        try:
            self.get_jwks_url()
            self.get_issuer()

            if self.is_production():
                # Additional validation for production
                if not self.clerk_jwks_url or not self.clerk_issuer:
                    raise ValueError(
                        "Production environment requires explicit JWKS URL and issuer configuration"
                    )

            logger.info("Clerk configuration validated successfully")
            return True

        except Exception as e:
            logger.error(f"Clerk configuration validation failed: {e}")
            raise


# Global configuration instance
_config: ClerkConfig | None = None


def get_clerk_config() -> ClerkConfig:
    """Get the global Clerk configuration instance.
    
    Returns:
        ClerkConfig: The configured Clerk settings
        
    Raises:
        ValueError: If configuration is not initialized or invalid
    """
    global _config

    if _config is None:
        try:
            _config = ClerkConfig()
            _config.validate_configuration()
            logger.info("Clerk configuration initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Clerk configuration: {e}")
            raise ValueError(f"Clerk configuration error: {e}")

    return _config


def reset_clerk_config():
    """Reset the global configuration instance.
    
    This is primarily used for testing purposes.
    """
    global _config
    _config = None
