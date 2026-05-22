import httpx
import base64
from datetime import datetime
from fastapi import HTTPException
from ..config import settings
import logging

logger = logging.getLogger(__name__)

MPESA_SANDBOX_URL    = "https://sandbox.safaricom.co.ke"
MPESA_PRODUCTION_URL = "https://api.safaricom.co.ke"

# Use sandbox in development
MPESA_BASE_URL = MPESA_SANDBOX_URL if settings.APP_ENV == "development" else MPESA_PRODUCTION_URL


async def get_mpesa_access_token() -> str:
    """Get OAuth access token from M-Pesa"""
    credentials = base64.b64encode(
        f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}".encode()
    ).decode()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials",
            headers={"Authorization": f"Basic {credentials}"}
        )

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to get M-Pesa token")

    return response.json()["access_token"]


def generate_mpesa_password() -> tuple:
    """Generate M-Pesa password and timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password  = base64.b64encode(
        f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}".encode()
    ).decode()
    return password, timestamp


async def initiate_stk_push(phone: str, amount: float, description: str = "Payment") -> dict:
    """
    Initiate M-Pesa STK Push (Lipa Na M-Pesa)
    Sends payment prompt to user's phone
    """
    token               = await get_mpesa_access_token()
    password, timestamp = generate_mpesa_password()

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password":          password,
        "Timestamp":         timestamp,
        "TransactionType":   "CustomerPayBillOnline",
        "Amount":            int(amount),
        "PartyA":            phone,
        "PartyB":            settings.MPESA_SHORTCODE,
        "PhoneNumber":       phone,
        "CallBackURL":       settings.MPESA_CALLBACK_URL,
        "AccountReference":  settings.APP_NAME,
        "TransactionDesc":   description,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json"
            },
            json=payload
        )

    result = response.json()
    logger.info(f"STK Push response: {result}")

    if result.get("ResponseCode") != "0":
        raise HTTPException(
            status_code=400,
            detail=result.get("ResponseDescription", "Payment initiation failed")
        )

    return {
        "checkout_request_id": result.get("CheckoutRequestID"),
        "merchant_request_id": result.get("MerchantRequestID"),
        "response_code":       result.get("ResponseCode"),
        "response_description": result.get("ResponseDescription"),
        "customer_message":    result.get("CustomerMessage"),
    }


def process_mpesa_callback(callback_data: dict) -> dict:
    """
    Process M-Pesa callback after payment
    Called by M-Pesa servers at your callback URL
    """
    body = callback_data.get("Body", {}).get("stkCallback", {})

    result_code = body.get("ResultCode")
    result_desc = body.get("ResultDesc")

    if result_code != 0:
        return {
            "success":     False,
            "message":     result_desc,
            "result_code": result_code
        }

    # extract payment details from callback metadata
    metadata = {}
    items    = body.get("CallbackMetadata", {}).get("Item", [])
    for item in items:
        metadata[item["Name"]] = item.get("Value")

    return {
        "success":        True,
        "amount":         metadata.get("Amount"),
        "transaction_id": metadata.get("MpesaReceiptNumber"),
        "phone":          str(metadata.get("PhoneNumber")),
        "transaction_date": metadata.get("TransactionDate"),
    }
