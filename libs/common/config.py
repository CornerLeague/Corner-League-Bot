# Copyright (c) 2024 Sports Media Platform
# Licensed under the MIT License

"""Configuration management using Pydantic settings."""

import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
load_dotenv()


class DatabaseSettings(BaseSettings):
    """Database connection settings"""
    
    model_config = SettingsConfigDict(
        env_prefix='DATABASE_',
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    url: str
    pool_size: int = 20
    max_overflow: int = 30
    pool_recycle: int = 3600
    echo: bool = False


class RedisSettings(BaseSettings):
    """Redis configuration"""
    
    model_config = SettingsConfigDict(
        env_prefix='REDIS_',
        env_file='.env',
        extra='ignore'
    )
    
    url: str = "redis://localhost:6379/0"
    max_connections: int = 20
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True


class ElasticsearchSettings(BaseSettings):
    """Elasticsearch configuration"""
    
    model_config = SettingsConfigDict(
        env_prefix='ELASTICSEARCH_',
        env_file='.env',
        extra='ignore'
    )
    
    url: str = "http://localhost:9200"
    username: Optional[str] = None
    password: Optional[str] = None
    verify_certs: bool = True
    timeout: int = 30
    max_retries: int = 3


class DeepSeekSettings(BaseSettings):
    """DeepSeek AI configuration"""
    
    model_config = SettingsConfigDict(
        env_prefix='DEEPSEEK_',
        env_file='.env',
        extra='ignore'
    )
    
    api_key: str
    base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"
    max_tokens: int = 4000
    temperature: float = 0.1
    timeout: int = 60
    max_retries: int = 3
    
    # Budget controls
    daily_token_limit: int = 1000000
    cost_per_token: float = 0.000002  # $0.002 per 1K tokens


class EvomiSettings(BaseSettings):
    """Evomi proxy configuration"""
    
    model_config = SettingsConfigDict(
        env_prefix='EVOMI_',
        env_file='.env',
        extra='ignore'
    )
    
    proxy_user: str
    proxy_pass: str
    endpoints: List[str] = [
        "rotating-residential.evomi.com:8000",
        "datacenter.evomi.com:8001",
        "mobile.evomi.com:8002"
    ]
    
    # Budget controls
    daily_budget: float = 100.0
    cost_per_gb: float = 3.0
    
    # Rate limiting
    requests_per_second: int = 10
    concurrent_requests: int = 50


class SecuritySettings(BaseSettings):
    """Security configuration"""
    
    model_config = SettingsConfigDict(
        env_prefix='SECURITY_',
        env_file='.env',
        extra='ignore'
    )
    
    # JWT settings
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # API key settings
    api_key_length: int = 32
    api_key_prefix: str = "smp_"
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    rate_limit_per_day: int = 10000
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    cors_allow_credentials: bool = True
    
    # Security headers
    hsts_max_age: int = 31536000  # 1 year
    csp_policy: str = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"


class CrawlingSettings(BaseSettings):
    """Web crawling configuration"""
    
    model_config = SettingsConfigDict(
        env_prefix='CRAWLING_',
        env_file='.env',
        extra='ignore'
    )
    
    # Request settings
    user_agent: str = "SportsMediaBot/1.0 (+https://sportsmedia.com/bot)"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Rate limiting
    default_delay: float = 1.0
    max_concurrent_per_domain: int = 5
    respect_robots_txt: bool = True
    
    # Content limits
    max_content_size: int = 10 * 1024 * 1024  # 10MB
    max_redirects: int = 10
    
    # Quality filters
    min_content_length: int = 200
    max_content_length: int = 50000
    blocked_domains: List[str] = []


class SearchSettings(BaseSettings):
    """Search configuration"""
    
    model_config = SettingsConfigDict(
        env_prefix='SEARCH_',
        env_file='.env',
        extra='ignore'
    )
    
    # PostgreSQL FTS settings
    default_config: str = "english"
    max_results: int = 1000
    default_limit: int = 20
    
    # Elasticsearch settings (when enabled)
    use_elasticsearch: bool = False
    es_index_name: str = "sports_content"
    es_shards: int = 1
    es_replicas: int = 0
    
    # Caching
    cache_ttl_seconds: int = 300  # 5 minutes
    cache_results: bool = True


class QualitySettings(BaseSettings):
    """Content quality configuration"""
    
    model_config = SettingsConfigDict(
        env_prefix='QUALITY_',
        env_file='.env',
        extra='ignore'
    )
    
    # Quality thresholds
    min_score: float = 0.3
    default_threshold: float = 0.6
    premium_threshold: float = 0.8
    
    # Shadow mode (for testing quality filters)
    shadow_mode: bool = True
    shadow_rejection_rate_target: float = 0.25
    
    # Source reputation
    reputation_decay_days: int = 30
    min_reputation_score: float = 0.1
    max_reputation_score: float = 1.0


class TrendingSettings(BaseSettings):
    """Trending detection configuration"""
    
    model_config = SettingsConfigDict(
        env_prefix='TRENDING_',
        env_file='.env',
        extra='ignore'
    )
    
    # Time windows
    short_window_hours: int = 1
    medium_window_hours: int = 6
    long_window_hours: int = 24
    
    # Thresholds
    min_burst_ratio: float = 2.0
    min_trend_score: float = 0.5
    min_occurrences: int = 5
    
    # Cooldown
    cooldown_hours: int = 6
    max_terms: int = 100


class MonitoringSettings(BaseSettings):
    """Monitoring and observability configuration"""
    
    model_config = SettingsConfigDict(
        env_prefix='MONITORING_',
        env_file='.env',
        extra='ignore'
    )
    
    # Prometheus
    prometheus_port: int = 8001
    prometheus_path: str = "/metrics"
    
    # Sentry
    sentry_dsn: Optional[str] = None
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = 0.1
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    log_file: Optional[str] = None
    
    # Health checks
    health_check_timeout: int = 5


class Settings(BaseSettings):
    """Main application settings"""
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    # Environment
    environment: str = "development"
    debug: bool = False
    testing: bool = False
    
    # Application
    app_name: str = "Corner League Bot"
    app_version: str = "1.0.0"
    api_prefix: str = "/v1"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    # Component settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    elasticsearch: ElasticsearchSettings = Field(default_factory=ElasticsearchSettings)
    deepseek: DeepSeekSettings = Field(default_factory=DeepSeekSettings)
    evomi: EvomiSettings = Field(default_factory=EvomiSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    crawling: CrawlingSettings = Field(default_factory=CrawlingSettings)
    search: SearchSettings = Field(default_factory=SearchSettings)
    quality: QualitySettings = Field(default_factory=QualitySettings)
    trending: TrendingSettings = Field(default_factory=TrendingSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)

    @validator("environment")
    def validate_environment(cls, v):
        if v not in ["development", "staging", "production"]:
            raise ValueError("Environment must be development, staging, or production")
        return v

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        return self.testing


# Global settings instance (lazy loaded)
_settings = None


def get_settings() -> Settings:
    """Get application settings"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Use get_settings() function to access settings


# Feature flags
class FeatureFlags:
    """Feature flags for gradual rollout"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self._cache: Dict[str, Any] = {}
    
    async def is_enabled(self, flag_name: str, default: bool = False) -> bool:
        """Check if a feature flag is enabled"""
        
        # Check cache first
        if flag_name in self._cache:
            return self._cache[flag_name]
        
        # Check Redis if available
        if self.redis_client:
            try:
                value = await self.redis_client.get(f"feature_flag:{flag_name}")
                if value is not None:
                    enabled = value.decode().lower() == "true"
                    self._cache[flag_name] = enabled
                    return enabled
            except Exception:
                pass  # Fall back to default
        
        # Check environment variable
        env_var = f"FEATURE_{flag_name.upper()}"
        env_value = os.getenv(env_var)
        if env_value is not None:
            enabled = env_value.lower() in ("true", "1", "yes", "on")
            self._cache[flag_name] = enabled
            return enabled
        
        return default
    
    async def set_flag(self, flag_name: str, enabled: bool) -> None:
        """Set a feature flag value"""
        
        self._cache[flag_name] = enabled
        
        if self.redis_client:
            try:
                await self.redis_client.set(
                    f"feature_flag:{flag_name}",
                    "true" if enabled else "false",
                    ex=86400  # 24 hours
                )
            except Exception:
                pass  # Fail silently
    
    def clear_cache(self) -> None:
        """Clear feature flag cache"""
        self._cache.clear()


# Common feature flags
FEATURE_FLAGS = {
    "ELASTICSEARCH_SEARCH": False,
    "TRENDING_DISCOVERY": True,
    "QUALITY_ENFORCEMENT": False,  # Start in shadow mode
    "AI_SUMMARIZATION": True,
    "SOCIAL_MEDIA_MONITORING": False,
    "ADVANCED_PERSONALIZATION": False,
    "REAL_TIME_UPDATES": False,
    "PREMIUM_SOURCES_ONLY": False,
    "CHAOS_TESTING": False,
}


def create_feature_flags(redis_client=None) -> FeatureFlags:
    """Create feature flags instance"""
    return FeatureFlags(redis_client)

