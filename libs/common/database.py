# Copyright (c) 2024 Sports Media Platform
# Licensed under the MIT License

"""Database models, connection management, and migration utilities."""

import asyncio
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import UUID, uuid4

import asyncpg
import aiosqlite
import click
from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID as PGUUID
from sqlalchemy.types import TypeDecorator, String as SQLString
import json
import uuid
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)

Base = declarative_base()


# Database Models
class Source(Base):
    """Content source (website, RSS feed, etc.)"""

    __tablename__ = "sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False, unique=True)
    base_url = Column(String(500), nullable=False)
    source_type = Column(String(50), nullable=False)  # rss, sitemap, html, api
    
    # Crawling configuration
    crawl_frequency = Column(Integer, default=3600)  # seconds
    is_active = Column(Boolean, default=True)
    robots_txt_url = Column(String(500))
    sitemap_url = Column(String(500))
    rss_url = Column(String(500))
    
    # Quality and reputation
    quality_tier = Column(Integer, default=2)  # 1=premium, 2=quality, 3=discovery
    reputation_score = Column(Float, default=0.5)
    success_rate = Column(Float, default=1.0)
    avg_response_time = Column(Float, default=0.0)
    
    # Metadata
    language = Column(String(10), default="en")
    country = Column(String(10))
    sports_focus = Column(JSON)  # ["nba", "nfl", etc.]
    content_selectors = Column(JSON)  # CSS selectors for extraction
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_crawled = Column(DateTime)
    
    # Relationships
    content_items = relationship("ContentItem", back_populates="source")
    ingestion_jobs = relationship("IngestionJob", back_populates="source")

    __table_args__ = (
        Index("idx_sources_domain", "domain"),
        Index("idx_sources_active_tier", "is_active", "quality_tier"),
        Index("idx_sources_last_crawled", "last_crawled"),
    )


class ContentItem(Base):
    """Individual piece of content (article, post, etc.)"""

    __tablename__ = "content_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_id = Column(String(36), ForeignKey("sources.id"), nullable=False)
    
    # URLs and identification
    original_url = Column(String(1000), nullable=False)
    canonical_url = Column(String(1000), nullable=False)
    content_hash = Column(String(64), nullable=False)  # SHA-256 of normalized content
    
    # Content
    title = Column(String(500), nullable=False)
    text = Column(Text)
    byline = Column(String(200))
    summary = Column(Text)
    
    # Metadata
    published_at = Column(DateTime)
    language = Column(String(10), default="en")
    word_count = Column(Integer, default=0)
    image_url = Column(String(1000))
    
    # Sports-specific
    sports_keywords = Column(JSON)  # ["basketball", "Lakers", "LeBron James"]
    entities = Column(JSON)  # {"teams": [...], "players": [...], "leagues": [...]}
    content_type = Column(String(50))  # game_recap, analysis, breaking_news, etc.
    
    # Quality and ranking
    quality_score = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    engagement_score = Column(Float, default=0.0)
    
    # Processing status
    extraction_status = Column(String(20), default="pending")  # pending, success, failed, partial
    last_extracted = Column(DateTime)
    retry_count = Column(Integer, default=0)
    last_error = Column(Text)
    
    # Search
    # search_vector = Column(TSVECTOR)  # PostgreSQL-specific, disabled for SQLite
    
    # Flags
    is_active = Column(Boolean, default=True)
    is_duplicate = Column(Boolean, default=False)
    is_spam = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    source = relationship("Source", back_populates="content_items")
    quality_signals = relationship("QualitySignal", back_populates="content_item")
    user_interactions = relationship("UserInteraction", back_populates="content_item")

    __table_args__ = (
        UniqueConstraint("canonical_url", name="uq_content_canonical_url"),
        UniqueConstraint("content_hash", name="uq_content_hash"),
        Index("idx_content_published", "published_at"),
        Index("idx_content_quality", "quality_score"),
        Index("idx_content_source_active", "source_id", "is_active"),
        # Index("idx_content_search_vector", "search_vector", postgresql_using="gin"),  # PostgreSQL-specific
        # Index("idx_content_sports_keywords", "sports_keywords", postgresql_using="gin"),  # PostgreSQL-specific
    )


class IngestionJob(Base):
    """Tracks ingestion/crawling jobs"""

    __tablename__ = "ingestion_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_id = Column(String(36), ForeignKey("sources.id"), nullable=False)
    
    # Job details
    job_type = Column(String(50), nullable=False)  # discovery, crawl, extract, backfill
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    
    # Progress tracking
    items_discovered = Column(Integer, default=0)
    items_processed = Column(Integer, default=0)
    items_successful = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Results and errors
    result_summary = Column(JSON)
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    source = relationship("Source", back_populates="ingestion_jobs")

    __table_args__ = (
        Index("idx_ingestion_source_status", "source_id", "status"),
        Index("idx_ingestion_created", "created_at"),
    )


class QualitySignal(Base):
    """Quality signals for content items"""

    __tablename__ = "quality_signals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    content_item_id = Column(String(36), ForeignKey("content_items.id"), nullable=False)
    
    # Signal details
    signal_type = Column(String(50), nullable=False)  # source_reputation, freshness, depth, etc.
    signal_value = Column(Float, nullable=False)
    signal_weight = Column(Float, default=1.0)
    
    # Metadata
    computed_at = Column(DateTime, default=func.now())
    algorithm_version = Column(String(20))
    
    # Relationships
    content_item = relationship("ContentItem", back_populates="quality_signals")

    __table_args__ = (
        Index("idx_quality_content_type", "content_item_id", "signal_type"),
        Index("idx_quality_computed", "computed_at"),
    )


class TrendingTerm(Base):
    """Trending terms and topics"""

    __tablename__ = "trending_terms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Term details
    term = Column(String(200), nullable=False)
    normalized_term = Column(String(200), nullable=False)
    term_type = Column(String(50))  # player, team, league, event, etc.
    
    # Trending metrics
    count_1h = Column(Integer, default=0)
    count_6h = Column(Integer, default=0)
    count_24h = Column(Integer, default=0)
    burst_ratio = Column(Float, default=0.0)
    trend_score = Column(Float, default=0.0)
    
    # Status
    is_trending = Column(Boolean, default=False)
    trend_start = Column(DateTime)
    trend_peak = Column(DateTime)
    
    # Metadata
    related_terms = Column(JSON)  # ["related", "terms"]
    sports_context = Column(JSON)  # {"sport": "nba", "teams": [...]}
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_seen = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("normalized_term", name="uq_trending_term"),
        Index("idx_trending_burst", "burst_ratio"),
        Index("idx_trending_active", "is_trending", "trend_score"),
        Index("idx_trending_updated", "updated_at"),
    )


class User(Base):
    """User accounts and preferences"""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Authentication
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Profile
    username = Column(String(50), unique=True)
    full_name = Column(String(200))
    avatar_url = Column(String(500))
    
    # Preferences
    favorite_teams = Column(JSON)  # ["Lakers", "Patriots", etc.]
    favorite_sports = Column(JSON)  # ["nba", "nfl", etc.]
    content_preferences = Column(JSON)  # {"types": [...], "sources": [...]}
    notification_settings = Column(JSON)
    
    # Personalization
    quality_threshold = Column(Float, default=0.6)
    personalization_score = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    
    # Relationships
    interactions = relationship("UserInteraction", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_username", "username"),
        Index("idx_users_active", "is_active"),
    )


class UserInteraction(Base):
    """User interactions with content"""

    __tablename__ = "user_interactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    content_item_id = Column(String(36), ForeignKey("content_items.id"), nullable=False)
    
    # Interaction details
    interaction_type = Column(String(50), nullable=False)  # view, click, share, save, like
    duration_seconds = Column(Float)
    scroll_depth = Column(Float)  # 0.0 to 1.0
    
    # Context
    referrer = Column(String(500))
    user_agent = Column(String(500))
    ip_address = Column(String(45))
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="interactions")
    content_item = relationship("ContentItem", back_populates="user_interactions")

    __table_args__ = (
        Index("idx_interactions_user_content", "user_id", "content_item_id"),
        Index("idx_interactions_type_created", "interaction_type", "created_at"),
    )


class APIKey(Base):
    """API keys for external access"""

    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Key details
    key_hash = Column(String(255), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Permissions and limits
    scopes = Column(JSON)  # ["read:content", "write:preferences", etc.]
    rate_limit_per_hour = Column(Integer, default=1000)
    rate_limit_per_day = Column(Integer, default=10000)
    
    # Usage tracking
    total_requests = Column(Integer, default=0)
    last_used = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="api_keys")

    __table_args__ = (
        Index("idx_api_keys_hash", "key_hash"),
        Index("idx_api_keys_active", "is_active"),
    )


class SystemConfig(Base):
    """System configuration and feature flags"""

    __tablename__ = "system_config"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(Text)
    config_type = Column(String(50), default="string")  # string, int, float, bool, json
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# Pydantic Models for API
class SourceCreate(BaseModel):
    name: str
    domain: str
    base_url: str
    source_type: str
    crawl_frequency: int = 3600
    language: str = "en"
    country: Optional[str] = None
    sports_focus: Optional[List[str]] = None


class SourceResponse(BaseModel):
    id: UUID
    name: str
    domain: str
    base_url: str
    source_type: str
    is_active: bool
    quality_tier: int
    reputation_score: float
    created_at: datetime
    last_crawled: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContentItemResponse(BaseModel):
    id: UUID
    title: str
    byline: Optional[str] = None
    summary: Optional[str] = None
    canonical_url: str
    published_at: Optional[datetime] = None
    quality_score: float
    sports_keywords: Optional[List[str]] = None
    content_type: Optional[str] = None
    source_name: str = Field(..., description="Name of the source")
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: Optional[str] = None
    sports: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    content_types: Optional[List[str]] = None
    quality_threshold: Optional[float] = None
    date_range: Optional[Dict[str, str]] = None
    sort_by: str = "relevance"
    limit: int = Field(20, ge=1, le=100)
    cursor: Optional[str] = None


class SearchResponse(BaseModel):
    items: List[ContentItemResponse]
    total_count: int
    has_more: bool
    next_cursor: Optional[str] = None
    search_time_ms: float


class TrendingTopicResponse(BaseModel):
    term: str
    trend_score: float
    burst_ratio: float
    count_24h: int
    related_terms: List[str]
    sports_context: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# Database Connection Management
class DatabaseManager:
    """Manages database connections and operations"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        self.session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_tables(self) -> None:
        """Create all database tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """Drop all database tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def close(self) -> None:
        """Close database connections"""
        await self.engine.dispose()


# Connection Pool for Raw Queries
class ConnectionPool:
    """Database connection pool supporting both PostgreSQL and SQLite"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
        self.is_sqlite = database_url.startswith('sqlite')

    async def initialize(self) -> None:
        """Initialize connection pool"""
        if self.is_sqlite:
            # For SQLite, we don't use a connection pool
            # The connection will be created per operation
            pass
        else:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60,
            )

    async def close(self) -> None:
        """Close connection pool"""
        if self.pool:
            await self.pool.close()

    async def execute(self, query: str, *args) -> str:
        """Execute a query"""
        if self.is_sqlite:
            # SQLite operations are handled by SQLAlchemy, not raw connections
            raise NotImplementedError("Raw SQLite operations not supported. Use SQLAlchemy session instead.")
        
        if not self.pool:
            raise RuntimeError("Connection pool not initialized")
        
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch query results"""
        if self.is_sqlite:
            # SQLite operations are handled by SQLAlchemy, not raw connections
            raise NotImplementedError("Raw SQLite operations not supported. Use SQLAlchemy session instead.")
        
        if not self.pool:
            raise RuntimeError("Connection pool not initialized")
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch single row"""
        if self.is_sqlite:
            # SQLite operations are handled by SQLAlchemy, not raw connections
            raise NotImplementedError("Raw SQLite operations not supported. Use SQLAlchemy session instead.")
        
        if not self.pool:
            raise RuntimeError("Connection pool not initialized")
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def fetchval(self, query: str, *args) -> Any:
        """Fetch single value"""
        if self.is_sqlite:
            # SQLite operations are handled by SQLAlchemy, not raw connections
            raise NotImplementedError("Raw SQLite operations not supported. Use SQLAlchemy session instead.")
        
        if not self.pool:
            raise RuntimeError("Connection pool not initialized")
        
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)


# CLI Commands
@click.group()
def cli():
    """Database management commands"""
    pass


@cli.command()
@click.option("--database-url", required=True, help="Database URL")
def create_tables(database_url: str):
    """Create all database tables"""
    async def _create():
        manager = DatabaseManager(database_url)
        await manager.create_tables()
        await manager.close()
        click.echo("Tables created successfully")

    asyncio.run(_create())


@cli.command()
@click.option("--database-url", required=True, help="Database URL")
def drop_tables(database_url: str):
    """Drop all database tables"""
    async def _drop():
        manager = DatabaseManager(database_url)
        await manager.drop_tables()
        await manager.close()
        click.echo("Tables dropped successfully")

    asyncio.run(_drop())


@cli.command()
@click.option("--database-url", required=True, help="Database URL")
def migrate(database_url: str):
    """Run database migrations"""
    # This would integrate with Alembic
    click.echo("Running migrations...")
    # TODO: Implement Alembic integration


def migrate_cli():
    """Entry point for migration CLI"""
    cli()


if __name__ == "__main__":
    cli()

