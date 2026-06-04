from .celery_tasks import celery_app
from app.services.sms_service import (
    send_otp_sms,
    send_payment_confirmation_sms,
    send_sms_via_africastalking
)
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_sms_task(self, phone: str, message: str):
    """
    Queue SMS via Africa's Talking — JUST CALLS SERVICE (no logic duplication)
    Works across Kenya, Nigeria, Uganda, Tanzania, etc.
    """
    try:
        result = send_sms_via_africastalking(phone, message)
        return result
    except Exception as exc:
        logger.error(f"SMS failed to {phone}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3)
def send_otp_sms_task(self, phone: str, otp: str):
    """Queue OTP SMS — JUST CALLS SERVICE (no logic duplication)"""
    try:
        result = send_otp_sms(phone, otp)
        return result
    except Exception as exc:
        logger.error(f"Failed to send OTP to {phone}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3)
def send_payment_confirmation_sms_task(self, phone: str, amount: float, transaction_id: str):
    """Queue payment SMS — JUST CALLS SERVICE (no logic duplication)"""
    try:
        result = send_payment_confirmation_sms(phone, amount, transaction_id)
        return result
    except Exception as exc:
        logger.error(f"Failed to send payment confirmation to {phone}: {exc}")
        raise self.retry(exc=exc)



