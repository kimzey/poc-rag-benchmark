"""
Phase 4: Auth Models — User types, roles, permissions
"""
from enum import Enum
from typing import Set
from pydantic import BaseModel


class UserType(str, Enum):
    employee = "employee"
    customer = "customer"
    admin = "admin"
    service = "service"


class AccessLevel(str, Enum):
    """Document access levels — stored as metadata on every document."""
    customer_kb = "customer_kb"      # Visible to customer + employee + admin
    internal_kb = "internal_kb"      # Visible to employee + admin only
    confidential_kb = "confidential_kb"  # Admin only


# What access levels each user type can see
USER_ACCESS_LEVELS: dict[UserType, Set[AccessLevel]] = {
    UserType.customer: {AccessLevel.customer_kb},
    UserType.employee: {AccessLevel.customer_kb, AccessLevel.internal_kb},
    UserType.admin: {AccessLevel.customer_kb, AccessLevel.internal_kb, AccessLevel.confidential_kb},
    UserType.service: {AccessLevel.customer_kb, AccessLevel.internal_kb},
}


class Permission(str, Enum):
    # Document permissions
    doc_read = "doc:read"
    doc_upload = "doc:upload"
    doc_delete = "doc:delete"
    doc_index = "doc:index"
    # Chat permissions
    chat_query = "chat:query"
    # Admin permissions
    user_manage = "user:manage"
    system_config = "system:config"
    analytics_read = "analytics:read"


# RBAC: role → set of permissions
ROLE_PERMISSIONS: dict[UserType, Set[Permission]] = {
    UserType.customer: {
        Permission.doc_read,
        Permission.chat_query,
    },
    UserType.employee: {
        Permission.doc_read,
        Permission.doc_upload,
        Permission.doc_index,
        Permission.chat_query,
        Permission.analytics_read,
    },
    UserType.admin: {p for p in Permission},  # all permissions
    UserType.service: {
        Permission.doc_read,
        Permission.chat_query,
    },
}


class User(BaseModel):
    user_id: str
    username: str
    user_type: UserType
    is_active: bool = True

    @property
    def permissions(self) -> Set[Permission]:
        return ROLE_PERMISSIONS.get(self.user_type, set())

    @property
    def allowed_access_levels(self) -> Set[AccessLevel]:
        return USER_ACCESS_LEVELS.get(self.user_type, set())

    def has_permission(self, permission: Permission) -> bool:
        return permission in self.permissions


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: str
    username: str
    user_type: UserType
