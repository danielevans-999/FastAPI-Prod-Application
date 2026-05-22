from ..celery_app import celery_app
from ..database import SessionLocal
from .. import models
import logging

logger = logging.getLogger(__name__)


# ── Notification Tasks ────────────────────────────────────

@celery_app.task
def create_notification(user_id: int, title: str, message: str, type: str = "info"):
    """Create in-app notification for a user"""
    db = SessionLocal()
    try:
        notification = models.Notification(
            user_id = user_id,
            title   = title,
            message = message,
            type    = type
        )
        db.add(notification)
        db.commit()
        logger.info(f"Notification created for user {user_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create notification: {e}")
    finally:
        db.close()


@celery_app.task
def broadcast_notification(title: str, message: str, role: str = None):
    """
    Broadcast notification to all users or specific role
    role=None → all users
    role="admin" → only admins
    """
    db = SessionLocal()
    try:
        query = db.query(models.User).filter(models.User.is_active == True)
        if role:
            query = query.filter(models.User.role == role)

        users = query.all()

        notifications = [
            models.Notification(
                user_id = user.id,
                title   = title,
                message = message,
                type    = "info"
            )
            for user in users
        ]

        db.bulk_save_objects(notifications)
        db.commit()
        logger.info(f"Broadcast notification sent to {len(notifications)} users")

    except Exception as e:
        db.rollback()
        logger.error(f"Broadcast failed: {e}")
    finally:
        db.close()


# ── Data Pipeline Tasks ───────────────────────────────────

@celery_app.task
def cleanup_expired_sessions():
    """
    Scheduled task — runs daily at 2am
    Cleans up expired WebSocket sessions
    """
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(days=1)

        deleted = db.query(models.WebSocketSession).filter(
            models.WebSocketSession.created_at < cutoff,
            models.WebSocketSession.is_active == False
        ).delete()

        db.commit()
        logger.info(f"Cleaned up {deleted} expired sessions")

    except Exception as e:
        db.rollback()
        logger.error(f"Cleanup failed: {e}")
    finally:
        db.close()


@celery_app.task
def process_bulk_data(data: list, operation: str):
    """
    Generic data pipeline task
    operation: "import", "export", "transform"
    """
    logger.info(f"Processing {len(data)} records — operation: {operation}")
    # Add your data processing logic here
    results = []
    for record in data:
        # process each record
        results.append({"processed": True, "record": record})

    logger.info(f"Pipeline complete — {len(results)} records processed")
    return {"processed": len(results), "operation": operation}
