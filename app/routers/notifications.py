from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.models import User
from app.schemas.schemas import SendEmailRequest, SendSMSRequest, MessageResponse
from app.tasks.celery_tasks import send_email_task, send_sms_task

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.post("/email", response_model=MessageResponse)
def send_email(
    request: SendEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin)
):
    """Send email — admin only. Runs in background so request returns immediately."""
    background_tasks.add_task(
        send_email_task,
        to=request.to,
        subject=request.subject,
        body=request.body
    )
    return {"message": f"Email queued to {request.to}"}


@router.post("/sms", response_model=MessageResponse)
def send_sms(
    request: SendSMSRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin)
):
    """Send SMS via Africa's Talking — admin only"""
    background_tasks.add_task(
        send_sms_task,
        phone=request.phone,
        message=request.message
    )
    return {"message": f"SMS queued to {request.phone}"}


@router.post("/welcome/{user_id}", response_model=MessageResponse)
def send_welcome_notification(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Send welcome email + SMS to a user"""
    from app.models.models import User as UserModel
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")

    background_tasks.add_task(
        send_email_task,
        to=user.email,
        subject="Welcome to our platform!",
        body=f"Hi {user.first_name}, welcome aboard!"
    )
    if user.phone:
        background_tasks.add_task(
            send_sms_task,
            phone=user.phone,
            message=f"Hi {user.first_name}! Welcome. Your account is ready."
        )

    return {"message": "Welcome notifications queued"}
