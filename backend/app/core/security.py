"""
Security utilities for authentication, authorization, and encryption.

This module provides JWT token handling, password hashing, role-based access control,
and HIPAA-compliant security measures.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import hashlib
import structlog
from cryptography.fernet import Fernet

from app.core.config import settings
from app.models.user import User
from app.services.user import UserService

logger = structlog.get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Security
security = HTTPBearer(auto_error=False)

# Encryption for sensitive data
encryption_key = settings.ENCRYPTION_KEY.encode()
cipher_suite = Fernet(encryption_key)


class SecurityManager:
    """Centralized security management."""
    
    def __init__(self):
        self.user_service = UserService()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
    def create_refresh_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            
            if payload.get("type") != token_type:
                raise JWTError("Invalid token type")
            
            username: str = payload.get("sub")
            if username is None:
                raise JWTError("Token missing subject")
            
            return payload
            
        except JWTError as e:
            logger.warning("Token verification failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data using Fernet encryption."""
        return cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        return cipher_suite.decrypt(encrypted_data.encode()).decode()
    
    def generate_session_id(self) -> str:
        """Generate secure session ID."""
        return secrets.token_urlsafe(32)
    
    def hash_for_audit(self, data: str) -> str:
        """Hash data for audit logging (one-way)."""
        return hashlib.sha256(data.encode()).hexdigest()


# Global security manager instance
security_manager = SecurityManager()


# Role-based access control
class RoleChecker:
    """Role-based access control decorator."""
    
    def __init__(self, required_roles: List[str]):
        self.required_roles = required_roles
    
    def __call__(self, user: User = Depends(get_current_user)) -> User:
        """Check if user has required roles."""
        if not any(role.name in self.required_roles for role in user.roles):
            logger.warning(
                "Access denied - insufficient permissions",
                user_id=user.id,
                required_roles=self.required_roles,
                user_roles=[role.name for role in user.roles]
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user


# Permission checks
def require_roles(roles: List[str]):
    """Decorator to require specific roles."""
    return RoleChecker(roles)


# Common role requirements
require_admin = require_roles(["admin"])
require_clinician = require_roles(["admin", "clinician", "nurse"])
require_staff = require_roles(["admin", "clinician", "nurse", "receptionist"])


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    request: Request = None
) -> User:
    """Get current authenticated user."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token
    payload = security_manager.verify_token(credentials.credentials)
    username = payload.get("sub")
    
    # Get user from database
    user_service = UserService()
    user = await user_service.get_by_username(username)
    
    if user is None:
        logger.warning("User not found for valid token", username=username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        logger.warning("Inactive user attempted access", user_id=user.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    # Log access for audit
    if settings.AUDIT_LOGGING:
        await log_access(request, user, "api_access")
    
    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user


async def log_access(request: Request, user: User, action: str):
    """Log user access for HIPAA audit requirements."""
    from app.models.audit_log import AuditLog
    from app.services.audit import AuditService
    
    audit_service = AuditService()
    
    audit_entry = AuditLog(
        user_id=user.id,
        action=action,
        resource=str(request.url),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        session_id=getattr(request.state, "session_id", None),
        timestamp=datetime.utcnow(),
        success=True
    )
    
    await audit_service.create_audit_log(audit_entry)


class SessionManager:
    """Manage user sessions with Redis."""
    
    def __init__(self):
        from app.db.redis import get_redis
        self.redis = get_redis()
    
    async def create_session(self, user_id: str, device_info: Dict[str, Any]) -> str:
        """Create new user session."""
        session_id = security_manager.generate_session_id()
        session_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "device_info": device_info,
            "last_activity": datetime.utcnow().isoformat()
        }
        
        await self.redis.setex(
            f"session:{session_id}",
            settings.SESSION_EXPIRE_MINUTES * 60,
            security_manager.encrypt_sensitive_data(str(session_data))
        )
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        encrypted_data = await self.redis.get(f"session:{session_id}")
        if not encrypted_data:
            return None
        
        try:
            decrypted_data = security_manager.decrypt_sensitive_data(
                encrypted_data.decode()
            )
            return eval(decrypted_data)  # Use proper JSON parsing in production
        except Exception:
            return None
    
    async def update_session_activity(self, session_id: str):
        """Update session last activity timestamp."""
        session_data = await self.get_session(session_id)
        if session_data:
            session_data["last_activity"] = datetime.utcnow().isoformat()
            await self.redis.setex(
                f"session:{session_id}",
                settings.SESSION_EXPIRE_MINUTES * 60,
                security_manager.encrypt_sensitive_data(str(session_data))
            )
    
    async def revoke_session(self, session_id: str):
        """Revoke user session."""
        await self.redis.delete(f"session:{session_id}")
    
    async def revoke_all_user_sessions(self, user_id: str):
        """Revoke all sessions for a user."""
        keys = await self.redis.keys(f"session:*")
        for key in keys:
            session_data = await self.get_session(key.decode().split(":")[1])
            if session_data and session_data.get("user_id") == user_id:
                await self.redis.delete(key)


# Global session manager
session_manager = SessionManager()


# Rate limiting
class RateLimiter:
    """Simple rate limiting using Redis."""
    
    def __init__(self, max_requests: int = 100, window_minutes: int = 1):
        self.max_requests = max_requests
        self.window_seconds = window_minutes * 60
        from app.db.redis import get_redis
        self.redis = get_redis()
    
    async def is_allowed(self, key: str) -> bool:
        """Check if request is allowed within rate limit."""
        current_count = await self.redis.get(f"rate_limit:{key}")
        
        if current_count is None:
            await self.redis.setex(
                f"rate_limit:{key}", 
                self.window_seconds, 
                1
            )
            return True
        
        if int(current_count) >= self.max_requests:
            return False
        
        await self.redis.incr(f"rate_limit:{key}")
        return True


# Input validation and sanitization
def sanitize_input(input_data: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    import html
    import re
    
    # HTML escape
    sanitized = html.escape(input_data)
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', sanitized)
    
    # Limit length
    sanitized = sanitized[:1000]
    
    return sanitized.strip()


def validate_medical_id(medical_id: str) -> bool:
    """Validate medical ID format (Aadhaar, MRN, etc.)."""
    import re
    
    # Aadhaar number validation (12 digits)
    aadhaar_pattern = r'^[2-9]{1}[0-9]{3}\s?[0-9]{4}\s?[0-9]{4}$'
    if re.match(aadhaar_pattern, medical_id.replace(" ", "")):
        return True
    
    # Medical Record Number (alphanumeric, 6-20 chars)
    mrn_pattern = r'^[A-Za-z0-9]{6,20}$'
    if re.match(mrn_pattern, medical_id):
        return True
    
    return False
