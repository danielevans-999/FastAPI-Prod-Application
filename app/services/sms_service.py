import httpx
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def send_sms_via_africastalking(phone: str, message: str):
    """
    Core SMS sender using Africa's Talking — PURE FUNCTION
    No Celery decorators, no async — just business logic
    """
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


def send_otp_sms(phone: str, otp: str):
    """
    Send OTP via SMS — ALL BUSINESS LOGIC HERE (no duplication)
    """
    message = f"Your {settings.APP_NAME} verification code is: {otp}. Valid for 10 minutes."
    result = send_sms_via_africastalking(phone, message)
    logger.info(f"OTP sent to {phone}")
    return result


def send_payment_confirmation_sms(phone: str, amount: float, transaction_id: str):
    """
    Send payment confirmation SMS — ALL BUSINESS LOGIC HERE (no duplication)
    """
    message = (
        f"Payment confirmed. Amount: KES {amount:.2f}. "
        f"Transaction ID: {transaction_id}. "
        f"Thank you for using {settings.APP_NAME}."
    )
    result = send_sms_via_africastalking(phone, message)
    logger.info(f"Payment confirmation sent to {phone}")
    return result

