"""
Patient management API endpoints.

This module provides CRUD operations for patient data with
FHIR compliance, validation, and audit logging.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import structlog
from uuid import UUID

from app.core.security import get_current_user, require_staff
from app.core.config import settings
from app.db.session import get_db
from app.models.patient import Patient
from app.models.user import User
from app.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientSearchParams,
    PatientFHIR
)
from app.services.patient import PatientService
from app.services.audit import AuditService
from app.utils.pagination import paginate
from app.utils.validation import validate_aadhaar, validate_phone

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    *,
    db: AsyncSession = Depends(get_db),
    patient_in: PatientCreate,
    current_user: User = Depends(require_staff),
    request: Request
) -> Patient:
    """
    Create a new patient record.
    
    Requires staff-level permissions and performs comprehensive validation
    including Aadhaar verification and duplicate detection.
    """
    logger.info("Creating new patient", user_id=current_user.id)
    
    # Validate input data
    if patient_in.aadhaar and not validate_aadhaar(patient_in.aadhaar):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Aadhaar number format"
        )
    
    if patient_in.phone and not validate_phone(patient_in.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format"
        )
    
    patient_service = PatientService(db)
    
    # Check for duplicates
    existing_patient = None
    if patient_in.aadhaar:
        existing_patient = await patient_service.get_by_aadhaar(patient_in.aadhaar)
    elif patient_in.phone:
        existing_patient = await patient_service.get_by_phone(patient_in.phone)
    
    if existing_patient:
        logger.warning("Duplicate patient registration attempt", 
                      existing_id=existing_patient.id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Patient already exists with this identifier",
            headers={"X-Existing-Patient-ID": str(existing_patient.id)}
        )
    
    try:
        # Create patient
        patient = await patient_service.create(
            obj_in=patient_in,
            created_by=current_user.id
        )
        
        # Log creation for audit
        audit_service = AuditService(db)
        await audit_service.log_patient_action(
            user_id=current_user.id,
            patient_id=patient.id,
            action="create_patient",
            details={"patient_id": patient.patient_id},
            request=request
        )
        
        logger.info("Patient created successfully", 
                   patient_id=patient.patient_id,
                   created_by=current_user.id)
        
        return patient
        
    except Exception as e:
        logger.error("Failed to create patient", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create patient record"
        )


@router.get("/", response_model=Dict[str, Any])
async def list_patients(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
    params: PatientSearchParams = Depends(),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
) -> Dict[str, Any]:
    """
    List patients with search and pagination.
    
    Supports filtering by name, phone, Aadhaar, age range,
    and other demographic criteria.
    """
    logger.info("Listing patients", user_id=current_user.id, params=params.dict())
    
    patient_service = PatientService(db)
    
    try:
        # Build search filters
        filters = {}
        if params.search:
            filters["search"] = params.search
        if params.aadhaar:
            filters["aadhaar"] = params.aadhaar
        if params.phone:
            filters["phone"] = params.phone
        if params.age_min is not None:
            filters["age_min"] = params.age_min
        if params.age_max is not None:
            filters["age_max"] = params.age_max
        if params.gender:
            filters["gender"] = params.gender
        
        # Get patients with pagination
        patients, total = await patient_service.search(
            filters=filters,
            skip=skip,
            limit=limit
        )
        
        return {
            "patients": patients,
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": (skip + limit) < total
        }
        
    except Exception as e:
        logger.error("Failed to list patients", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patient list"
        )


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    *,
    db: AsyncSession = Depends(get_db),
    patient_id: str,
    current_user: User = Depends(require_staff),
    include_encounters: bool = Query(False),
    include_vitals: bool = Query(False)
) -> Patient:
    """
    Get patient details by ID.
    
    Optionally includes related encounters and vital signs data.
    """
    logger.info("Getting patient details", patient_id=patient_id, user_id=current_user.id)
    
    patient_service = PatientService(db)
    
    try:
        patient = await patient_service.get_by_patient_id(
            patient_id=patient_id,
            include_encounters=include_encounters,
            include_vitals=include_vitals
        )
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        return patient
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get patient", patient_id=patient_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patient details"
        )


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    *,
    db: AsyncSession = Depends(get_db),
    patient_id: str,
    patient_update: PatientUpdate,
    current_user: User = Depends(require_staff),
    request: Request
) -> Patient:
    """
    Update patient information.
    
    Tracks changes for audit logging and validates
    updated information.
    """
    logger.info("Updating patient", patient_id=patient_id, user_id=current_user.id)
    
    patient_service = PatientService(db)
    
    try:
        # Get existing patient
        patient = await patient_service.get_by_patient_id(patient_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Validate updated data
        if patient_update.aadhaar and patient_update.aadhaar != patient.aadhaar:
            if not validate_aadhaar(patient_update.aadhaar):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Aadhaar number format"
                )
            
            # Check for duplicates
            existing = await patient_service.get_by_aadhaar(patient_update.aadhaar)
            if existing and existing.id != patient.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Another patient already has this Aadhaar number"
                )
        
        # Update patient
        updated_patient = await patient_service.update(
            db_obj=patient,
            obj_in=patient_update
        )
        
        # Log update for audit
        audit_service = AuditService(db)
        await audit_service.log_patient_action(
            user_id=current_user.id,
            patient_id=patient.id,
            action="update_patient",
            details=patient_update.dict(exclude_unset=True),
            request=request
        )
        
        logger.info("Patient updated successfully", patient_id=patient_id)
        
        return updated_patient
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update patient", patient_id=patient_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update patient record"
        )


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    *,
    db: AsyncSession = Depends(get_db),
    patient_id: str,
    current_user: User = Depends(require_staff),
    request: Request,
    force: bool = Query(False)  # For hard delete
):
    """
    Delete or deactivate patient record.
    
    By default performs soft delete (deactivation).
    Use force=true for hard delete (admin only).
    """
    logger.info("Deleting patient", patient_id=patient_id, user_id=current_user.id, force=force)
    
    if force and not current_user.has_role("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hard delete requires admin privileges"
        )
    
    patient_service = PatientService(db)
    
    try:
        patient = await patient_service.get_by_patient_id(patient_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        if force:
            await patient_service.delete(patient.id)
            action = "hard_delete_patient"
        else:
            await patient_service.deactivate(patient.id)
            action = "deactivate_patient"
        
        # Log deletion for audit
        audit_service = AuditService(db)
        await audit_service.log_patient_action(
            user_id=current_user.id,
            patient_id=patient.id,
            action=action,
            details={"force": force},
            request=request
        )
        
        logger.info("Patient deleted successfully", patient_id=patient_id, force=force)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete patient", patient_id=patient_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete patient record"
        )


@router.get("/{patient_id}/fhir", response_model=PatientFHIR)
async def get_patient_fhir(
    *,
    db: AsyncSession = Depends(get_db),
    patient_id: str,
    current_user: User = Depends(require_staff)
) -> Dict[str, Any]:
    """
    Get patient data in FHIR format.
    
    Returns patient information structured according to
    HL7 FHIR R4 Patient resource specification.
    """
    logger.info("Getting patient FHIR data", patient_id=patient_id, user_id=current_user.id)
    
    patient_service = PatientService(db)
    
    try:
        patient = await patient_service.get_by_patient_id(patient_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        fhir_data = patient.to_fhir_dict()
        return fhir_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get FHIR data", patient_id=patient_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve FHIR data"
        )


@router.post("/search", response_model=List[PatientResponse])
async def search_patients(
    *,
    db: AsyncSession = Depends(get_db),
    search_params: Dict[str, Any],
    current_user: User = Depends(require_staff),
    limit: int = Query(20, ge=1, le=100)
) -> List[Patient]:
    """
    Advanced patient search with multiple criteria.
    
    Supports complex queries with demographic, clinical,
    and geographic filters.
    """
    logger.info("Advanced patient search", user_id=current_user.id, params=search_params)
    
    patient_service = PatientService(db)
    
    try:
        patients = await patient_service.advanced_search(
            criteria=search_params,
            limit=limit
        )
        
        return patients
        
    except Exception as e:
        logger.error("Advanced search failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search operation failed"
        )


@router.get("/{patient_id}/timeline")
async def get_patient_timeline(
    *,
    db: AsyncSession = Depends(get_db),
    patient_id: str,
    current_user: User = Depends(require_staff),
    include_vitals: bool = Query(True),
    include_encounters: bool = Query(True),
    include_assessments: bool = Query(True),
    days: int = Query(30, ge=1, le=365)
) -> Dict[str, Any]:
    """
    Get patient clinical timeline.
    
    Returns chronological view of patient's medical history
    including encounters, vital signs, and assessments.
    """
    logger.info("Getting patient timeline", patient_id=patient_id, user_id=current_user.id)
    
    patient_service = PatientService(db)
    
    try:
        timeline = await patient_service.get_timeline(
            patient_id=patient_id,
            days=days,
            include_vitals=include_vitals,
            include_encounters=include_encounters,
            include_assessments=include_assessments
        )
        
        return timeline
        
    except Exception as e:
        logger.error("Failed to get timeline", patient_id=patient_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patient timeline"
        )


@router.post("/{patient_id}/merge")
async def merge_patients(
    *,
    db: AsyncSession = Depends(get_db),
    patient_id: str,
    merge_with_id: str,
    current_user: User = Depends(require_staff),
    request: Request
) -> PatientResponse:
    """
    Merge two patient records.
    
    Combines duplicate patient records while preserving
    all clinical data and maintaining audit trail.
    """
    logger.info("Merging patients", 
               primary_id=patient_id, 
               merge_id=merge_with_id, 
               user_id=current_user.id)
    
    if not current_user.has_role("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient merge requires admin privileges"
        )
    
    patient_service = PatientService(db)
    
    try:
        merged_patient = await patient_service.merge_patients(
            primary_id=patient_id,
            merge_id=merge_with_id,
            merged_by=current_user.id
        )
        
        # Log merge for audit
        audit_service = AuditService(db)
        await audit_service.log_patient_action(
            user_id=current_user.id,
            patient_id=merged_patient.id,
            action="merge_patients",
            details={
                "primary_id": patient_id,
                "merged_id": merge_with_id
            },
            request=request
        )
        
        logger.info("Patients merged successfully", result_id=merged_patient.patient_id)
        
        return merged_patient
        
    except Exception as e:
        logger.error("Failed to merge patients", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Patient merge operation failed"
        )
