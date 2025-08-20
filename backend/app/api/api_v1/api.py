"""
API Router configuration for version 1 endpoints.

This module aggregates all API endpoints and configures
the main router with proper tags and dependencies.
"""

from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    auth,
    patients,
    triage,
    vitals,
    queue,
    devices,
    analytics,
    admin,
    clinical_support
)

api_router = APIRouter()

# Authentication endpoints
api_router.include_router(
    auth.router, 
    prefix="/auth", 
    tags=["authentication"]
)

# Patient management endpoints
api_router.include_router(
    patients.router, 
    prefix="/patients", 
    tags=["patients"]
)

# Triage assessment endpoints
api_router.include_router(
    triage.router, 
    prefix="/triage", 
    tags=["triage"]
)

# Vital signs endpoints
api_router.include_router(
    vitals.router, 
    prefix="/vitals", 
    tags=["vitals"]
)

# Queue management endpoints
api_router.include_router(
    queue.router, 
    prefix="/queue", 
    tags=["queue"]
)

# Device integration endpoints
api_router.include_router(
    devices.router, 
    prefix="/devices", 
    tags=["devices"]
)

# Clinical decision support endpoints
api_router.include_router(
    clinical_support.router, 
    prefix="/clinical", 
    tags=["clinical-support"]
)

# Analytics and reporting endpoints
api_router.include_router(
    analytics.router, 
    prefix="/analytics", 
    tags=["analytics"]
)

# Administrative endpoints
api_router.include_router(
    admin.router, 
    prefix="/admin", 
    tags=["admin"]
)
