from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import logging
from typing import Any, Dict

from libs.auth.middleware import ClerkAuthMiddleware
from libs.common.config import get_config
from libs.api.response import ApiResponse

# Import route modules
from . import auth_routes, questionnaire_routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sports Media Platform API",
    description="AI-powered sports media discovery and personalization platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with standardized response format."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse.error(
            message=exc.detail,
            error_code=f"HTTP_{exc.status_code}"
        ).model_dump()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors with detailed field information."""
    logger.warning(f"Validation error: {exc.errors()} - {request.url}")
    return JSONResponse(
        status_code=422,
        content=ApiResponse.error(
            message="Validation failed",
            error_code="VALIDATION_ERROR",
            details=exc.errors()
        ).model_dump()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with generic error response."""
    logger.error(f"Unhandled exception: {str(exc)} - {request.url}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ApiResponse.error(
            message="Internal server error",
            error_code="INTERNAL_ERROR"
        ).model_dump()
    )

# CORS Configuration
config = get_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication Middleware
app.add_middleware(ClerkAuthMiddleware)

# Include routers
app.include_router(auth_routes.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(questionnaire_routes.router, prefix="/api/questionnaire", tags=["Questionnaire"])

# Health check endpoint
@app.get("/health", response_model=ApiResponse[Dict[str, str]])
async def health_check():
    """Health check endpoint."""
    return ApiResponse.success(data={"status": "healthy", "version": "1.0.0"})

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Sports Media Platform API",
        version="1.0.0",
        description="AI-powered sports media discovery and personalization platform",
        routes=app.routes,
    )
    
    # Add custom schema components
    openapi_schema["components"]["schemas"]["ApiResponse"] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "data": {"type": "object"},
            "message": {"type": "string"},
            "error_code": {"type": "string"},
            "details": {"type": "object"}
        },
        "required": ["success"]
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
