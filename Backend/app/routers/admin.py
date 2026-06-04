from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.models import User, Payment, FileUpload, Notification
from app.schemas.schemas import UserResponse, MessageResponse
from typing import List

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])


@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Admin dashboard — system stats overview"""
    total_users    = db.query(func.count(User.id)).scalar()
    active_users   = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    total_payments = db.query(func.count(Payment.id)).scalar()
    total_revenue  = db.query(func.sum(Payment.amount)).filter(Payment.status == "success").scalar() or 0
    total_files    = db.query(func.count(FileUpload.id)).scalar()

    return {
        "stats": {
            "total_users":    total_users,
            "active_users":   active_users,
            "inactive_users": total_users - active_users,
            "total_payments": total_payments,
            "total_revenue":  total_revenue,
            "total_files":    total_files,
        }
    }


@router.get("/users", response_model=List[UserResponse])
def admin_list_users(
    skip: int = 0,
    limit: int = 50,
    role: str = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """List all users with optional role filter"""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.offset(skip).limit(limit).all()


@router.put("/users/{user_id}/activate", response_model=MessageResponse)
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    from fastapi import HTTPException
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    db.commit()
    return {"message": f"User {user.username} activated"}


@router.put("/users/{user_id}/role", response_model=MessageResponse)
def change_user_role(
    user_id: int,
    new_role: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    from fastapi import HTTPException
    if new_role not in ["admin", "staff", "user"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = new_role
    db.commit()
    return {"message": f"User {user.username} role changed to {new_role}"}
