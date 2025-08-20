"""
Core configuration settings for the Smart Triage Kiosk System.

This module contains all configuration settings, environment variables,
and application constants used throughout the system.
"""

import os
from typing import List, Optional, Any, Dict
from pydantic import BaseSettings, validator, PostgresDsn, HttpUrl
import secrets


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Basic App Settings
    PROJECT_NAME: str = "Smart Triage Kiosk System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Security Settings
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    SESSION_EXPIRE_MINUTES: int = 60 * 8  # 8 hours
    ALGORITHM: str = "HS256"
    
    # Server Settings
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    ALLOWED_HOSTS: List[str] = ["*"]
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://localhost:3000",
        "https://localhost:8080"
    ]
    
    # Database Settings
    DATABASE_URL: Optional[PostgresDsn] = None
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_USER: str = "triware"
    DATABASE_PASSWORD: str = "password"
    DATABASE_NAME: str = "triware_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # SQLite for offline mode
    SQLITE_URL: str = "sqlite:///./triware_offline.db"
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_EXPIRE: int = 60 * 60 * 24  # 24 hours
    
    # Celery Settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_ALWAYS_EAGER: bool = False
    
    # ML/AI Settings
    ML_MODEL_PATH: str = "./models"
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MODEL_UPDATE_INTERVAL: int = 3600  # 1 hour
    INFERENCE_TIMEOUT: int = 30  # seconds
    BATCH_PREDICTION_SIZE: int = 100
    
    # Healthcare Standards
    FHIR_VERSION: str = "4.0.1"
    HL7_VERSION: str = "2.8"
    SNOMED_VERSION: str = "2023-09"
    ICD10_VERSION: str = "2023"
    
    # Triage Categories
    TRIAGE_CATEGORIES: Dict[str, Dict[str, Any]] = {
        "red": {"name": "Immediate", "priority": 1, "max_wait_minutes": 0},
        "orange": {"name": "Very Urgent", "priority": 2, "max_wait_minutes": 15},
        "yellow": {"name": "Urgent", "priority": 3, "max_wait_minutes": 60},
        "green": {"name": "Routine", "priority": 4, "max_wait_minutes": 240},
        "blue": {"name": "Non-urgent", "priority": 5, "max_wait_minutes": 480}
    }
    
    # Device Integration
    BLE_SCAN_TIMEOUT: int = 30
    DEVICE_CONNECTION_TIMEOUT: int = 10
    VITALS_VALIDATION_RANGES: Dict[str, Dict[str, float]] = {
        "heart_rate": {"min": 30, "max": 220},
        "systolic_bp": {"min": 60, "max": 250},
        "diastolic_bp": {"min": 30, "max": 150},
        "temperature": {"min": 32.0, "max": 45.0},  # Celsius
        "spo2": {"min": 70, "max": 100},
        "weight": {"min": 1, "max": 500},  # kg
        "height": {"min": 30, "max": 250}  # cm
    }
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".pdf", ".dicom"]
    
    # MinIO/S3 Settings
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    BUCKET_NAME: str = "triware-storage"
    
    # Notification Settings
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    
    # Monitoring Settings
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_ENABLED: bool = True
    METRICS_PORT: int = 9090
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None
    
    # Internationalization
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: List[str] = ["en", "hi", "ta", "te", "kn", "ml", "gu", "mr"]
    
    # Security & Compliance
    HIPAA_COMPLIANCE: bool = True
    AUDIT_LOGGING: bool = True
    ENCRYPTION_KEY: str = secrets.token_urlsafe(32)
    
    # Performance Settings
    CACHE_TTL: int = 3600  # 1 hour
    MAX_CONCURRENT_REQUESTS: int = 100
    REQUEST_TIMEOUT: int = 30
    
    # Development Settings
    RELOAD_ON_CHANGE: bool = False
    PROFILING_ENABLED: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """Assemble database URL from individual components if not provided."""
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("DATABASE_USER"),
            password=values.get("DATABASE_PASSWORD"),
            host=values.get("DATABASE_HOST"),
            port=str(values.get("DATABASE_PORT")),
            path=f"/{values.get('DATABASE_NAME') or ''}",
        )
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_allowed_origins(cls, v: str) -> List[str]:
        """Parse allowed origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("SUPPORTED_LANGUAGES", pre=True)
    def parse_supported_languages(cls, v: str) -> List[str]:
        """Parse supported languages from comma-separated string."""
        if isinstance(v, str):
            return [lang.strip() for lang in v.split(",")]
        return v


# Create global settings instance
settings = Settings()


# Feature flags
FEATURE_FLAGS = {
    "voice_recognition": True,
    "camera_vitals": False,  # Experimental
    "infection_control": True,
    "multilingual": True,
    "offline_mode": True,
    "device_integration": True,
    "ai_triage": True,
    "queue_management": True,
    "clinical_support": True,
    "analytics": True,
    "telemedicine": False,  # Future feature
}


# Medical constants
MEDICAL_CONSTANTS = {
    "pain_scale_max": 10,
    "fever_threshold_celsius": 37.8,
    "fever_threshold_fahrenheit": 100.0,
    "hypertension_systolic": 140,
    "hypertension_diastolic": 90,
    "hypotension_systolic": 90,
    "hypotension_diastolic": 60,
    "tachycardia_threshold": 100,
    "bradycardia_threshold": 60,
    "hypoxia_threshold": 94,
    "max_age": 120,
    "min_age": 0,
}


# Red flag symptoms that require immediate attention
RED_FLAG_SYMPTOMS = [
    "chest_pain_severe",
    "difficulty_breathing_severe",
    "unconscious",
    "severe_bleeding",
    "stroke_symptoms",
    "severe_allergic_reaction",
    "cardiac_arrest",
    "severe_trauma",
    "poisoning",
    "suicidal_ideation",
    "severe_abdominal_pain",
    "severe_headache_sudden",
    "high_fever_with_rash",
    "seizure_ongoing"
]


# Drug interaction severity levels
DRUG_INTERACTION_LEVELS = {
    "contraindicated": {"level": 1, "color": "red"},
    "major": {"level": 2, "color": "orange"},
    "moderate": {"level": 3, "color": "yellow"},
    "minor": {"level": 4, "color": "blue"},
    "unknown": {"level": 5, "color": "gray"}
}
