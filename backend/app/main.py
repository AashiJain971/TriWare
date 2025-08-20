"""
Smart Triage Kiosk System - Backend API

A comprehensive healthcare triage system with AI-powered risk assessment,
device integration, and offline-first architecture.
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
import structlog
import time
import uuid
from contextlib import asynccontextmanager

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.security import get_current_user
from app.db.session import engine
from app.db.base import Base
from app.core.celery_app import celery_app

# Setup structured logging
setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting Smart Triage Kiosk System API")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize ML models
    from app.ml.model_manager import ModelManager
    model_manager = ModelManager()
    await model_manager.initialize()
    
    # Start background tasks
    logger.info("API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API")
    await model_manager.cleanup()
    logger.info("API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Smart Triage Kiosk System API",
    description="""
    A comprehensive healthcare triage system with AI-powered risk assessment,
    device integration, and offline-first architecture.
    
    ## Features
    
    * **Patient Registration** - Multi-language support with voice guidance
    * **Symptom Assessment** - Dynamic symptom trees with adaptive questioning
    * **Device Integration** - BLE medical device connectivity
    * **AI Triage** - Hybrid ML models for accurate risk scoring
    * **Queue Management** - Real-time load balancing and notifications
    * **Clinical Support** - Drug interactions, guidelines, and protocols
    * **Offline-First** - Complete functionality without internet
    
    ## Security
    
    * HIPAA compliant with end-to-end encryption
    * JWT authentication with role-based access control
    * Comprehensive audit logging
    * Regular security assessments
    """,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Security Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=settings.SESSION_EXPIRE_MINUTES * 60
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID and Logging Middleware
@app.middleware("http")
async def add_request_id_and_logging(request: Request, call_next):
    """Add request ID and structured logging to all requests."""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Bind request context to logger
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        url=str(request.url),
        user_agent=request.headers.get("user-agent", ""),
        ip=request.client.host if request.client else ""
    )
    
    logger = structlog.get_logger(__name__)
    logger.info("Request started")
    
    # Add request ID to headers
    request.state.request_id = request_id
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            "Request completed",
            status_code=response.status_code,
            duration=f"{process_time:.4f}s"
        )
        
        response.headers["X-Request-ID"] = request_id
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            "Request failed",
            error=str(e),
            duration=f"{process_time:.4f}s",
            exc_info=True
        )
        raise


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured logging."""
    logger = structlog.get_logger(__name__)
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with structured logging."""
    logger = structlog.get_logger(__name__)
    logger.error(
        "Unhandled exception",
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    from app.services.health import HealthService
    
    health_service = HealthService()
    health_status = await health_service.check_all()
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    
    return JSONResponse(
        status_code=status_code,
        content=health_status
    )


# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from app.core.metrics import registry
    
    return Response(
        generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST
    )


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Smart Triage Kiosk System API",
        "version": "1.0.0",
        "description": "AI-powered healthcare triage system",
        "docs_url": "/docs",
        "health_check": "/health",
        "api_version": settings.API_V1_STR
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config=None  # Use our structured logging
    )
