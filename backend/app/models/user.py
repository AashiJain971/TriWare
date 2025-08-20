"""
User model for authentication and role-based access control.

This module defines user accounts, roles, and permissions for the
Smart Triage Kiosk System with HIPAA compliance.
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import List, Dict, Any

from app.db.base_class import Base


# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True)
)

# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id'), primary_key=True)
)


class User(Base):
    """
    User model for system authentication and authorization.
    
    Supports healthcare staff with role-based access control,
    audit logging, and HIPAA compliance features.
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Authentication
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Personal information
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    middle_name = Column(String(50), nullable=True)
    
    # Professional information
    employee_id = Column(String(20), unique=True, index=True, nullable=True)
    license_number = Column(String(50), nullable=True)  # Medical license
    department = Column(String(100), nullable=True)
    specialization = Column(String(100), nullable=True)
    
    # Contact information
    phone = Column(String(20), nullable=True)
    address = Column(JSON, nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    
    # Security
    last_login = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Multi-factor authentication
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255), nullable=True)
    backup_codes = Column(JSON, nullable=True)
    
    # Preferences
    preferred_language = Column(String(10), default="en")
    timezone = Column(String(50), default="Asia/Kolkata")
    notification_preferences = Column(JSON, nullable=True)
    
    # System metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    created_by_user = relationship("User", remote_side=[id])
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"
    
    @property
    def full_name(self) -> str:
        """Get formatted full name."""
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return " ".join(parts)
    
    @property
    def display_name(self) -> str:
        """Get display name with professional title if available."""
        name = self.full_name
        if self.specialization:
            return f"Dr. {name}" if "doctor" in self.get_role_names().lower() else name
        return name
    
    def get_permissions(self) -> List[str]:
        """Get all permissions for this user through their roles."""
        permissions = set()
        for role in self.roles:
            for permission in role.permissions:
                permissions.add(permission.name)
        return list(permissions)
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has specific permission."""
        return permission_name in self.get_permissions()
    
    def get_role_names(self) -> List[str]:
        """Get list of role names for this user."""
        return [role.name for role in self.roles]
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has specific role."""
        return role_name in self.get_role_names()
    
    def is_healthcare_provider(self) -> bool:
        """Check if user is a healthcare provider."""
        healthcare_roles = ["doctor", "nurse", "clinician", "physician_assistant"]
        return any(role in self.get_role_names() for role in healthcare_roles)
    
    def can_access_patient_data(self) -> bool:
        """Check if user can access patient data."""
        required_permissions = ["read_patient", "read_patient_data"]
        return any(self.has_permission(perm) for perm in required_permissions)
    
    def is_account_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False


class Role(Base):
    """
    Role model for role-based access control.
    
    Defines different user roles with associated permissions
    for fine-grained access control.
    """
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Role properties
    is_system_role = Column(Boolean, default=False)  # System-defined roles
    is_active = Column(Boolean, default=True)
    
    # Hierarchy and inheritance
    parent_role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    level = Column(Integer, default=0)  # Role hierarchy level
    
    # System metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    parent_role = relationship("Role", remote_side=[id])
    
    def __repr__(self):
        return f"<Role(name={self.name})>"
    
    def get_all_permissions(self) -> List[str]:
        """Get all permissions including inherited from parent roles."""
        permissions = set()
        
        # Add direct permissions
        for permission in self.permissions:
            permissions.add(permission.name)
        
        # Add inherited permissions from parent roles
        if self.parent_role:
            permissions.update(self.parent_role.get_all_permissions())
        
        return list(permissions)


class Permission(Base):
    """
    Permission model for granular access control.
    
    Defines specific actions that can be performed in the system.
    """
    __tablename__ = "permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Permission categorization
    resource = Column(String(50), nullable=False)  # patient, user, system, etc.
    action = Column(String(50), nullable=False)    # create, read, update, delete
    
    # System metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission(name={self.name})>"


class UserSession(Base):
    """Track user sessions for security and audit purposes."""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    
    # Session lifecycle
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Session status
    is_active = Column(Boolean, default=True)
    logout_reason = Column(String(50), nullable=True)  # manual, timeout, security
    
    # Location information (if available)
    location_data = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User")
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at
    
    def extend_session(self, minutes: int = 30):
        """Extend session expiry time."""
        from datetime import timedelta
        self.expires_at = datetime.utcnow() + timedelta(minutes=minutes)
        self.last_activity = datetime.utcnow()


# Default system roles and permissions
DEFAULT_ROLES = [
    {
        "name": "admin",
        "display_name": "System Administrator",
        "description": "Full system access and user management",
        "is_system_role": True
    },
    {
        "name": "doctor",
        "display_name": "Doctor/Physician",
        "description": "Medical professional with patient care access",
        "is_system_role": True
    },
    {
        "name": "nurse",
        "display_name": "Nurse",
        "description": "Nursing staff with patient care access",
        "is_system_role": True
    },
    {
        "name": "receptionist",
        "display_name": "Receptionist",
        "description": "Front desk staff with limited patient access",
        "is_system_role": True
    },
    {
        "name": "technician",
        "display_name": "Medical Technician",
        "description": "Technical staff for device management",
        "is_system_role": True
    }
]

DEFAULT_PERMISSIONS = [
    # Patient permissions
    {"name": "create_patient", "display_name": "Create Patient", "resource": "patient", "action": "create"},
    {"name": "read_patient", "display_name": "Read Patient", "resource": "patient", "action": "read"},
    {"name": "update_patient", "display_name": "Update Patient", "resource": "patient", "action": "update"},
    {"name": "delete_patient", "display_name": "Delete Patient", "resource": "patient", "action": "delete"},
    
    # Triage permissions
    {"name": "create_triage", "display_name": "Create Triage", "resource": "triage", "action": "create"},
    {"name": "read_triage", "display_name": "Read Triage", "resource": "triage", "action": "read"},
    {"name": "update_triage", "display_name": "Update Triage", "resource": "triage", "action": "update"},
    
    # Queue management permissions
    {"name": "manage_queue", "display_name": "Manage Queue", "resource": "queue", "action": "manage"},
    {"name": "view_queue", "display_name": "View Queue", "resource": "queue", "action": "read"},
    
    # System permissions
    {"name": "admin_access", "display_name": "Admin Access", "resource": "system", "action": "admin"},
    {"name": "view_analytics", "display_name": "View Analytics", "resource": "analytics", "action": "read"},
    {"name": "manage_devices", "display_name": "Manage Devices", "resource": "device", "action": "manage"},
    
    # User management permissions
    {"name": "create_user", "display_name": "Create User", "resource": "user", "action": "create"},
    {"name": "read_user", "display_name": "Read User", "resource": "user", "action": "read"},
    {"name": "update_user", "display_name": "Update User", "resource": "user", "action": "update"},
    {"name": "delete_user", "display_name": "Delete User", "resource": "user", "action": "delete"},
]
