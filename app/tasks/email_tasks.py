from .celery_tasks import celery_app
from app.services.email_service import (
    send_welcome_email,
    send_password_reset_email,
    send_notification_email,
    send_daily_reports
)
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email_task(self, email: str, username: str):
    """Queue welcome email — JUST CALLS SERVICE (no logic duplication)"""
    try:
        send_welcome_email(email, username)
    except Exception as exc:
        logger.error(f"Failed to send welcome email to {email}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email_task(self, email: str, reset_token: str):
    """Queue password reset email — JUST CALLS SERVICE (no logic duplication)"""
    try:
        send_password_reset_email(email, reset_token)
    except Exception as exc:
        logger.error(f"Failed to send password reset email to {email}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task
def send_daily_reports_task():
    """Scheduled task — send daily reports"""
    try:
        send_daily_reports()
    except Exception as exc:
        logger.error(f"Failed to send daily reports: {exc}")


@celery_app.task(bind=True, max_retries=3)
def send_notification_email_task(self, email: str, title: str, message: str):
    """Queue notification email — JUST CALLS SERVICE (no logic duplication)"""
    try:
        send_notification_email(email, title, message)
    except Exception as exc:
        logger.error(f"Failed to send notification email to {email}: {exc}")
        raise self.retry(exc=exc)



