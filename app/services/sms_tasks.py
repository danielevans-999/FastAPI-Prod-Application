from ..celery_app import celery_app
from ..config import settings
import httpx
import logging

logger = logging.getLogger(__name__)


def get_at_token() -> str:
    """Get Africa's Talking auth token"""
    return settings.AT_API_KEY


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_sms(self, phone: str, message: str):
    """
    Send SMS via Africa's Talking
    Works across Kenya, Nigeria, Uganda, Tanzania, etc.
    """
    try:
        response = httpx.post(
            "https://api.africastalking.com/version1/messaging",
            headers={
                "apiKey":       settings.AT_API_KEY,
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept":       "application/json",
            },
            data={
                "username": settings.AT_USERNAME,
                "to":       phone,
                "message":  message,
                "from":     settings.AT_SENDER_ID,
            }
        )

        result = response.json()
        logger.info(f"SMS sent to {phone}: {result}")
        return result

    except Exception as exc:
        logger.error(f"SMS failed to {phone}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3)
def send_otp_sms(self, phone: str, otp: str):
    """Send OTP via SMS"""
    message = f"Your {settings.APP_NAME} verification code is: {otp}. Valid for 10 minutes."
    return send_sms.delay(phone, message)


@celery_app.task(bind=True, max_retries=3)
def send_payment_confirmation_sms(self, phone: str, amount: float, transaction_id: str):
    """Send payment confirmation SMS"""
    message = (
        f"Payment confirmed. Amount: KES {amount:.2f}. "
        f"Transaction ID: {transaction_id}. "
        f"Thank you for using {settings.APP_NAME}."
    )
    return send_sms.delay(phone, message)
