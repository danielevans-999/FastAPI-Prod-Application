from celery import Celery
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# ── Celery App ────────────────────────────────────────────
celery_app = Celery(
    "fastapi_backend",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Africa/Nairobi",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,  # only ack after task completes
)


# ── Email Task ────────────────────────────────────────────

def send_email_task(to: str, subject: str, body: str):
    """Send email via Gmail SMTP — runs as background task"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = os.getenv("MAIL_FROM")
        msg["To"]      = to
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP(os.getenv("MAIL_SERVER", "smtp.gmail.com"), 587) as server:
            server.starttls()
            server.login(os.getenv("MAIL_USERNAME"), os.getenv("MAIL_PASSWORD"))
            server.sendmail(os.getenv("MAIL_FROM"), to, msg.as_string())

        print(f"Email sent to {to}")
        return {"status": "sent", "to": to}

    except Exception as e:
        print(f"Email failed: {e}")
        return {"status": "failed", "error": str(e)}


# ── SMS Task (Africa's Talking) ───────────────────────────

def send_sms_task(phone: str, message: str):
    """Send SMS via Africa's Talking — runs as background task"""
    try:
        import africastalking
        africastalking.initialize(
            username=os.getenv("AT_USERNAME"),
            api_key=os.getenv("AT_API_KEY")
        )
        sms = africastalking.SMS
        response = sms.send(message, [phone], sender_id=os.getenv("AT_SENDER_ID"))
        print(f"SMS sent to {phone}: {response}")
        return {"status": "sent", "to": phone}

    except ImportError:
        print("africastalking not installed: pip install africastalking")
        return {"status": "failed", "error": "africastalking not installed"}
    except Exception as e:
        print(f"SMS failed: {e}")
        return {"status": "failed", "error": str(e)}


# ── Celery Tasks (for heavy async jobs) ───────────────────

@celery_app.task(name="tasks.send_bulk_email")
def send_bulk_email(user_ids: list, subject: str, body: str):
    """Send email to multiple users — heavy job via Celery"""
    from app.core.database import SessionLocal
    from app.models.models import User

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        results = []
        for user in users:
            result = send_email_task(user.email, subject, body)
            results.append(result)
        return {"sent": len(results), "results": results}
    finally:
        db.close()


@celery_app.task(name="tasks.cleanup_expired_tokens")
def cleanup_expired_tokens():
    """Clean up expired blacklisted tokens — run daily via Celery beat"""
    from app.core.database import SessionLocal
    from app.models.models import TokenBlacklist
    from datetime import datetime

    db = SessionLocal()
    try:
        deleted = db.query(TokenBlacklist).filter(
            TokenBlacklist.expires_at < datetime.utcnow()
        ).delete()
        db.commit()
        print(f"Cleaned up {deleted} expired tokens")
        return {"deleted": deleted}
    finally:
        db.close()


# ── Celery Beat Schedule (cron jobs) ─────────────────────
celery_app.conf.beat_schedule = {
    "cleanup-expired-tokens-daily": {
        "task":     "tasks.cleanup_expired_tokens",
        "schedule": 86400,  # every 24 hours
    },
}
