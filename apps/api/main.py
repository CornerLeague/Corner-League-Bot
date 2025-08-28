# Copyright (c) 2024 Corner League Bot
# Licensed under the MIT License

"""
FastAPI main application with comprehensive sports media API endpoints.
Integrates with all backend services and provides production-ready API.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

from libs.common.config import get_settings
from libs.common.database import ConnectionPool, DatabaseManager
from libs.ingestion.crawler import WebCrawler
from libs.ingestion.extractor import ContentExtractor
from libs.quality.scorer import QualityGate
from libs.search.engine import SearchEngine, SearchQuery
from libs.search.trending import TrendingDiscoveryLoop
from libs.auth import ClerkAuthMiddleware, get_clerk_config, get_user_service
from libs.auth.decorators import require_auth, optional_auth, require_role
from .auth_routes import router as auth_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
settings = get_settings()
connection_pool: Optional[ConnectionPool] = None
db_manager: Optional[DatabaseManager] = None
search_engine: Optional[SearchEngine] = None
trending_loop: Optional[TrendingDiscoveryLoop] = None
quality_gate: Optional[QualityGate] = None
clerk_config = get_clerk_config()
user_service = get_user_service()


# Pydantic models
class ContentItem(BaseModel):
    """Content item response model"""
    id: str
    title: str
    byline: Optional[str] = None
    summary: Optional[str] = None
    canonical_url: str
    published_at: Optional[datetime] = None
    quality_score: float
    sports_keywords: List[str] = []
    content_type: Optional[str] = None
    image_url: Optional[str] = None
    source_name: str
    word_count: Optional[int] = None
    language: str = "en"
    search_score: Optional[float] = None
    search_rank: Optional[int] = None


class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field("", description="Search query text")
    sports: List[str] = Field([], description="Sports filter (e.g., ['basketball', 'nba'])")
    sources: List[str] = Field([], description="Source domains filter")
    content_types: List[str] = Field([], description="Content type filter")
    quality_threshold: Optional[float] = Field(None, description="Minimum quality score")
    date_range: Dict[str, str] = Field({}, description="Date range filter")
    sort_by: str = Field("relevance", description="Sort order: relevance, date, quality, popularity")
    limit: int = Field(20, description="Number of results", le=100)
    cursor: Optional[str] = Field(None, description="Pagination cursor")


class SearchResponse(BaseModel):
    """Search response model"""
    items: List[ContentItem]
    total_count: int
    has_more: bool
    next_cursor: Optional[str] = None
    search_time_ms: float
    engine: str
    from_cache: bool = False


class TrendingTerm(BaseModel):
    """Trending term model"""
    term: str
    normalized_term: str
    term_type: str
    count_1h: int
    count_6h: int
    count_24h: int
    burst_ratio: float
    trend_score: float
    is_trending: bool
    trend_start: Optional[datetime] = None
    trend_peak: Optional[datetime] = None
    last_seen: datetime
    related_terms: List[str] = []
    sports_context: Dict[str, Any] = {}


class SummaryRequest(BaseModel):
    """AI summary request model"""
    content_ids: List[str] = Field(..., description="List of content IDs to summarize")
    summary_type: str = Field("brief", description="Summary type: brief, detailed, analysis")
    focus_areas: List[str] = Field([], description="Areas to focus on in summary")
    max_length: int = Field(200, description="Maximum summary length in words", le=500)


class SummaryResponse(BaseModel):
    """AI summary response model"""
    summary: str
    confidence_score: float
    source_count: int
    generation_time_ms: float
    citations: List[Dict[str, Any]] = []
    focus_areas_covered: List[str] = []


class UserPreferences(BaseModel):
    """User preferences model"""
    favorite_teams: List[str] = []
    favorite_sports: List[str] = []
    content_types: List[str] = []
    quality_threshold: float = 0.5
    language: str = "en"
    notification_settings: Dict[str, bool] = {}


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, Dict[str, Any]]


# Middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request logging and timing middleware"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"{request.method} {request.url.path} - Start")
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = (time.time() - start_time) * 1000
            
            # Log response
            logger.info(f"{request.method} {request.url.path} - {response.status_code} in {duration:.1f}ms")
            
            # Add timing header
            response.headers["X-Response-Time"] = f"{duration:.1f}ms"
            
            return response
        
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"{request.method} {request.url.path} - Error in {duration:.1f}ms: {e}")
            raise


# Application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    
    global connection_pool, db_manager, search_engine, trending_loop, quality_gate
    
    # Startup
    logger.info("Starting Corner League Bot API...")
    
    try:
        # Initialize database connection pool
        connection_pool = ConnectionPool(settings.database.url)
        await connection_pool.initialize()
        logger.info("Database connection pool initialized")
        
        # Initialize database manager
        db_manager = DatabaseManager(settings.database.url)
        logger.info("Database manager initialized")
        
        # Initialize search engine
        search_engine = SearchEngine(settings, connection_pool, db_manager=db_manager)
        await search_engine.initialize()
        logger.info("Search engine initialized")
        
        # Initialize trending detection
        trending_loop = TrendingDiscoveryLoop(settings, connection_pool, db_manager=db_manager)
        logger.info("Trending detection initialized")
        
        # Initialize quality gate
        quality_gate = QualityGate(settings)
        logger.info("Quality gate initialized")
        
        logger.info("Corner League Bot API started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down Corner League Bot API...")
        
        if search_engine:
            await search_engine.close()
        
        if connection_pool:
            await connection_pool.close()
        
        logger.info("Corner League Bot API shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Corner League Bot API",
    description="AI-powered sports media aggregation and personalization platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ClerkAuthMiddleware)

# Include authentication routes
app.include_router(auth_router)

# Security (Clerk handles JWT validation)
security = HTTPBearer(auto_error=False)


# Dependency injection
async def get_connection_pool() -> ConnectionPool:
    """Get database connection pool"""
    if not connection_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    return connection_pool


async def get_search_engine() -> SearchEngine:
    """Get search engine"""
    if not search_engine:
        raise HTTPException(status_code=503, detail="Search engine not available")
    return search_engine


async def get_trending_loop() -> TrendingDiscoveryLoop:
    """Get trending detection loop"""
    if not trending_loop:
        raise HTTPException(status_code=503, detail="Trending detection not available")
    return trending_loop


async def get_quality_gate() -> QualityGate:
    """Get quality gate"""
    if not quality_gate:
        raise HTTPException(status_code=503, detail="Quality gate not available")
    return quality_gate


async def get_db_manager() -> DatabaseManager:
    """Get database manager"""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database manager not available")
    return db_manager


async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get current authenticated user from request context."""
    return getattr(request.state, 'user', None)


async def get_user_id(request: Request) -> Optional[str]:
    """Get current user ID from request context."""
    user = getattr(request.state, 'user', None)
    return user.get('sub') if user else None


# API Routes

@app.get("/api/health", response_model=HealthResponse)
async def health_check(
    db_manager: DatabaseManager = Depends(get_db_manager)
) -> HealthResponse:
    """Health check endpoint"""
    
    services = {}
    
    # Check database
    try:
        async for session in db_manager.get_session():
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            break  # Only need one iteration
        services["database"] = {"status": "healthy", "response_time_ms": 0}
    except Exception as e:
        services["database"] = {"status": "unhealthy", "error": str(e)}
    
    # Check search engine
    try:
        if search_engine:
            services["search"] = {"status": "healthy", "backend": "postgresql"}
        else:
            services["search"] = {"status": "unhealthy", "error": "Not initialized"}
    except Exception as e:
        services["search"] = {"status": "unhealthy", "error": str(e)}
    
    # Overall status
    overall_status = "healthy" if all(
        s.get("status") == "healthy" for s in services.values()
    ) else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        services=services
    )


@app.post("/api/search", response_model=SearchResponse)
async def search_content(
    request: SearchRequest,
    http_request: Request,
    engine: SearchEngine = Depends(get_search_engine),
    user_info: Optional[dict] = Depends(optional_auth)
) -> SearchResponse:
    """Search sports content"""
    
    try:
        # Track user activity if authenticated
        user_id = await get_user_id(http_request)
        if user_id:
            await user_service.track_activity(
                user_id=user_id,
                action="search",
                resource_type="content",
                resource_id=None,
                metadata={
                    "query": request.query,
                    "sports": request.sports,
                    "sources": request.sources,
                    "content_types": request.content_types,
                    "sort_by": request.sort_by,
                    "limit": request.limit
                }
            )
        
        # Create search query
        search_query = SearchQuery(
            query=request.query,
            sports=request.sports,
            sources=request.sources,
            content_types=request.content_types,
            quality_threshold=request.quality_threshold,
            date_range=request.date_range,
            sort_by=request.sort_by,
            limit=request.limit,
            cursor=request.cursor
        )
        
        # Execute search
        results = await engine.search(search_query)
        
        # Convert to response model with proper data processing
        items = []
        for item in results['items']:
            # Process JSON fields and handle None values
            processed_item = dict(item)
            
            # Handle sports_keywords - convert from string to list if needed
            if isinstance(processed_item.get('sports_keywords'), str):
                import json
                try:
                    processed_item['sports_keywords'] = json.loads(processed_item['sports_keywords'])
                except (json.JSONDecodeError, TypeError):
                    # If it's a comma-separated string, split it
                    processed_item['sports_keywords'] = [kw.strip() for kw in processed_item['sports_keywords'].split(',') if kw.strip()]
            elif processed_item.get('sports_keywords') is None:
                processed_item['sports_keywords'] = []
            
            # Handle language field
            if processed_item.get('language') is None:
                processed_item['language'] = 'en'
            
            # Ensure required fields have defaults
            processed_item.setdefault('source_name', 'Unknown')
            processed_item.setdefault('quality_score', 0.0)
            
            items.append(ContentItem(**processed_item))
        
        
        return SearchResponse(
            items=items,
            total_count=results['total_count'],
            has_more=results['has_more'],
            next_cursor=results.get('next_cursor'),
            search_time_ms=results['search_time_ms'],
            engine=results['engine'],
            from_cache=results.get('from_cache', False)
        )
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/api/content/{content_id}", response_model=ContentItem)
async def get_content(
    content_id: str,
    pool: ConnectionPool = Depends(get_connection_pool)
) -> ContentItem:
    """Get specific content item"""
    
    try:
        query = """
        SELECT 
            ci.id, ci.title, ci.byline, ci.summary, ci.canonical_url,
            ci.published_at, ci.quality_score, ci.sports_keywords,
            ci.content_type, ci.image_url, s.name as source_name,
            ci.word_count, ci.language
        FROM content_items ci
        JOIN sources s ON ci.source_id = s.id
        WHERE ci.id = $1 AND ci.is_active = true
        """
        
        row = await pool.fetchrow(query, content_id)
        
        if not row:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Process the row data similar to search endpoint
        processed_item = dict(row)
        
        # Handle sports_keywords - convert from string to list if needed
        if isinstance(processed_item.get('sports_keywords'), str):
            import json
            try:
                processed_item['sports_keywords'] = json.loads(processed_item['sports_keywords'])
            except (json.JSONDecodeError, TypeError):
                # If it's a comma-separated string, split it
                processed_item['sports_keywords'] = [kw.strip() for kw in processed_item['sports_keywords'].split(',') if kw.strip()]
        elif processed_item.get('sports_keywords') is None:
            processed_item['sports_keywords'] = []
        
        # Handle language field
        if processed_item.get('language') is None:
            processed_item['language'] = 'en'
        
        # Ensure required fields have defaults
        processed_item.setdefault('source_name', 'Unknown')
        processed_item.setdefault('quality_score', 0.0)
        
        return ContentItem(**processed_item)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get content error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get content: {str(e)}")


@app.get("/api/trending", response_model=List[TrendingTerm])
async def get_trending_terms(
    limit: int = Query(10, le=50),
    trending_service: TrendingDiscoveryLoop = Depends(get_trending_loop)
) -> List[TrendingTerm]:
    """Get currently trending sports terms"""
    
    try:
        trending_terms = await trending_service.detector.detect_trending()
        
        # Limit results
        trending_terms = trending_terms[:limit]
        
        # Convert to Pydantic models
        result = []
        for term in trending_terms:
            term_dict = term.to_dict()
            # Convert ISO strings back to datetime objects for Pydantic
            if term_dict['trend_start']:
                term_dict['trend_start'] = datetime.fromisoformat(term_dict['trend_start'])
            if term_dict['trend_peak']:
                term_dict['trend_peak'] = datetime.fromisoformat(term_dict['trend_peak'])
            term_dict['last_seen'] = datetime.fromisoformat(term_dict['last_seen'])
            
            result.append(TrendingTerm(**term_dict))
        
        return result
    
    except Exception as e:
        logger.error(f"Trending terms error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trending terms: {str(e)}")


@app.post("/api/summarize", response_model=SummaryResponse)
async def summarize_content(
    request: SummaryRequest,
    http_request: Request,
    pool: ConnectionPool = Depends(get_connection_pool),
    credentials: HTTPAuthorizationCredentials = Depends(require_auth)
) -> SummaryResponse:
    """Generate AI summary of content items"""
    
    try:
        start_time = time.time()
        
        # Get content items
        if not request.content_ids:
            raise HTTPException(status_code=400, detail="No content IDs provided")
        
        placeholders = ",".join([f"${i+1}" for i in range(len(request.content_ids))])
        query = f"""
        SELECT 
            ci.id, ci.title, ci.text, ci.byline, ci.canonical_url,
            ci.published_at, s.name as source_name, ci.sports_keywords
        FROM content_items ci
        JOIN sources s ON ci.source_id = s.id
        WHERE ci.id IN ({placeholders}) AND ci.is_active = true
        """
        
        rows = await pool.fetch(query, *request.content_ids)
        
        if not rows:
            raise HTTPException(status_code=404, detail="No content found")
        
        # Prepare content for summarization
        content_texts = []
        citations = []
        
        for row in rows:
            content_texts.append({
                'title': row['title'],
                'text': row['text'] or '',
                'source': row['source_name'],
                'url': row['canonical_url'],
                'published_at': row['published_at']
            })
            
            citations.append({
                'id': str(row['id']),
                'title': row['title'],
                'source': row['source_name'],
                'url': row['canonical_url'],
                'published_at': row['published_at'].isoformat() if row['published_at'] else None
            })
        
        # Generate summary using DeepSeek AI (placeholder implementation)
        summary_text = await generate_ai_summary(
            content_texts,
            request.summary_type,
            request.focus_areas,
            request.max_length
        )
        
        generation_time = (time.time() - start_time) * 1000
        
        # Track user activity
        user_id = await get_user_id(http_request)
        if user_id:
            await user_service.track_user_activity(
                user_id=user_id,
                action="summarize",
                resource_type="content_batch",
                resource_id=",".join(request.content_ids),
                metadata={
                    "summary_type": request.summary_type,
                    "content_count": len(rows),
                    "focus_areas": request.focus_areas
                }
            )
        
        return SummaryResponse(
            summary=summary_text,
            confidence_score=0.85,  # Placeholder
            source_count=len(rows),
            generation_time_ms=generation_time,
            citations=citations,
            focus_areas_covered=request.focus_areas
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")


@app.get("/api/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=2),
    limit: int = Query(5, le=10),
    engine: SearchEngine = Depends(get_search_engine)
) -> List[str]:
    """Get search suggestions"""
    
    try:
        suggestions = await engine.suggest(q, limit)
        return suggestions
    
    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@app.get("/api/stats")
async def get_platform_stats(
    pool: ConnectionPool = Depends(get_connection_pool),
    trending_service: TrendingDiscoveryLoop = Depends(get_trending_loop),
    quality_service: QualityGate = Depends(get_quality_gate)
) -> Dict[str, Any]:
    """Get platform statistics"""
    
    try:
        # Content stats
        content_stats = await pool.fetchrow("""
        SELECT 
            COUNT(*) as total_articles,
            COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as articles_24h,
            COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 hour') as articles_1h,
            AVG(quality_score) as avg_quality_score,
            COUNT(DISTINCT source_id) as active_sources
        FROM content_items
        WHERE is_active = true
        """)
        
        # Trending stats
        trending_stats = trending_service.detector.get_stats()
        
        # Quality stats
        quality_stats = quality_service.get_stats()
        
        return {
            'content': dict(content_stats) if content_stats else {},
            'trending': trending_stats,
            'quality': quality_stats,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


# Note: User preferences endpoints have been moved to auth_routes.py
# These endpoints are now handled by the dedicated authentication router
# with proper Clerk integration and user management


# Helper functions
async def generate_ai_summary(
    content_texts: List[Dict[str, Any]],
    summary_type: str,
    focus_areas: List[str],
    max_length: int
) -> str:
    """Generate AI summary using DeepSeek AI"""
    
    # Placeholder implementation
    # In production, this would call DeepSeek AI API
    
    if not content_texts:
        return "No content available for summarization."
    
    # Simple extractive summary for now
    titles = [content['title'] for content in content_texts]
    sources = list(set(content['source'] for content in content_texts))
    
    if summary_type == "brief":
        summary = f"Latest sports updates from {len(sources)} sources covering {', '.join(titles[:3])}..."
    elif summary_type == "detailed":
        summary = f"Comprehensive analysis of recent sports developments from {', '.join(sources)}. Key stories include: {', '.join(titles)}."
    else:
        summary = f"In-depth analysis of trending sports topics with insights from {len(content_texts)} articles across {len(sources)} trusted sources."
    
    # Truncate to max length
    words = summary.split()
    if len(words) > max_length:
        summary = ' '.join(words[:max_length]) + '...'
    
    return summary


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Development server
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

