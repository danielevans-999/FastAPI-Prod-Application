from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


# ═══════════════════════════════════════════════════════
# USER SCHEMAS
# ═══════════════════════════════════════════════════════

class UserRole(str, Enum):
    admin   = "admin"
    manager = "manager"
    user    = "user"
    
class UserCreate(BaseModel):
    username:   str
    email:      EmailStr
    first_name: str
    last_name:  str
    phone:      Optional[str] = None
    role:       Optional[UserRole] = UserRole.user
    password:   str

    @field_validator("password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("username")
    def username_alphanumeric(cls, v):
        if not v.replace("_", "").isalnum():
            raise ValueError("Username must be alphanumeric")
        return v.lower()


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name:  Optional[str] = None
    phone:      Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(BaseModel):
    id:         int
    username:   str
    email:      str
    first_name: str
    last_name:  str
    phone:      Optional[str]
    role:       str
    is_active:  bool
    avatar_url: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════
# AUTH SCHEMAS
# ═══════════════════════════════════════════════════════

class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"


class RegisterResponse(BaseModel):
    user:   UserResponse
    tokens: TokenResponse


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


# ═══════════════════════════════════════════════════════
# PAYMENT SCHEMAS
# ═══════════════════════════════════════════════════════

class PaymentInitiate(BaseModel):
    amount:      float
    currency:    str = "KES"
    description: Optional[str] = None
    phone:       Optional[str] = None  # for M-Pesa/mobile money

    @field_validator("amount")
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v


class PaymentResponse(BaseModel):
    id:             int
    reference:      str
    amount:         float
    currency:       str
    status:         str
    payment_method: Optional[str]
    gateway_ref:    Optional[str]
    description:    Optional[str]
    created_at:     datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════
# NOTIFICATION SCHEMAS
# ═══════════════════════════════════════════════════════

class SendEmailRequest(BaseModel):
    to:      EmailStr
    subject: str
    body:    str


class SendSMSRequest(BaseModel):
    phone:   str
    message: str


class NotificationResponse(BaseModel):
    id:         int
    type:       str
    subject:    Optional[str]
    message:    str
    status:     str
    sent_at:    Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════
# FILE SCHEMAS
# ═══════════════════════════════════════════════════════

class FileResponse(BaseModel):
    id:            int
    filename:      str
    original_name: str
    file_type:     str
    file_size:     int
    url:           Optional[str]
    created_at:    datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════
# AI SCHEMAS
# ═══════════════════════════════════════════════════════

class AIRequest(BaseModel):
    prompt:      str
    max_tokens:  Optional[int] = 500
    temperature: Optional[float] = 0.7


class AIResponse(BaseModel):
    response:     str
    tokens_used:  int
    model:        str


# ═══════════════════════════════════════════════════════
# GENERIC SCHEMAS
# ═══════════════════════════════════════════════════════

class MessageResponse(BaseModel):
    message: str
    data:    Optional[Any] = None


class PaginatedResponse(BaseModel):
    items:   List[Any]
    total:   int
    page:    int
    size:    int
    pages:   int
