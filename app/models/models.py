from sqlalchemy import (
    Column, Integer, String, Boolean,
    DateTime, Float, Text, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


# ── Enums ─────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    admin  = "admin"
    staff  = "staff"
    user   = "user"

class PaymentStatus(str, enum.Enum):
    pending   = "pending"
    success   = "success"
    failed    = "failed"
    refunded  = "refunded"

class NotificationStatus(str, enum.Enum):
    pending  = "pending"
    sent     = "sent"
    failed   = "failed"


# ── User ──────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id          = Column(Integer, primary_key=True, index=True)
    username    = Column(String(50),  unique=True, index=True, nullable=False)
    email       = Column(String(255), unique=True, index=True, nullable=False)
    first_name  = Column(String(100), nullable=False)
    last_name   = Column(String(100), nullable=False)
    phone       = Column(String(20),  nullable=True)
    role        = Column(String(20),  default="user", nullable=False)
    password    = Column(String(255), nullable=False)
    is_active   = Column(Boolean, default=True)
    avatar_url  = Column(String(500), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    # relationships
    payments      = relationship("Payment",      back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    files         = relationship("FileUpload",   back_populates="user")


# ── Payment ───────────────────────────────────────────────

class Payment(Base):
    __tablename__ = "payments"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    reference       = Column(String(100), unique=True, index=True)
    amount          = Column(Float, nullable=False)
    currency        = Column(String(10), default="KES")
    status          = Column(String(20), default="pending")
    payment_method  = Column(String(50), nullable=True)
    gateway_ref     = Column(String(200), nullable=True)  # from payment provider
    description     = Column(String(500), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="payments")


# ── Notification ──────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    type        = Column(String(20), nullable=False)  # email, sms, push
    subject     = Column(String(255), nullable=True)
    message     = Column(Text, nullable=False)
    status      = Column(String(20), default="pending")
    sent_at     = Column(DateTime(timezone=True), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")


# ── File Upload ───────────────────────────────────────────

class FileUpload(Base):
    __tablename__ = "file_uploads"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename     = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_type    = Column(String(100), nullable=False)
    file_size    = Column(Integer, nullable=False)  # bytes
    s3_key       = Column(String(500), nullable=True)   # S3 object key
    url          = Column(String(1000), nullable=True)  # public URL
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="files")


# ── Token Blacklist (for logout) ──────────────────────────

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id         = Column(Integer, primary_key=True, index=True)
    token      = Column(String(500), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
