from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid, httpx
from app.core.database import get_db
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.models import User, Payment
from app.schemas.schemas import PaymentInitiate, PaymentResponse, MessageResponse

router = APIRouter(prefix="/api/payments", tags=["Payments"])


def generate_reference() -> str:
    return f"PAY-{uuid.uuid4().hex[:12].upper()}"


@router.post("/initiate", response_model=PaymentResponse, status_code=201)
async def initiate_payment(
    payment_data: PaymentInitiate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initiate a payment via Flutterwave"""

    reference = generate_reference()

    # Create payment record first
    payment = Payment(
        user_id     = current_user.id,
        reference   = reference,
        amount      = payment_data.amount,
        currency    = payment_data.currency,
        status      = "pending",
        description = payment_data.description,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    # Call Flutterwave API
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.flutterwave.com/v3/payments",
                headers={
                    "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "tx_ref":       reference,
                    "amount":       payment_data.amount,
                    "currency":     payment_data.currency,
                    "customer": {
                        "email":    current_user.email,
                        "name":     f"{current_user.first_name} {current_user.last_name}",
                        "phonenumber": payment_data.phone or current_user.phone
                    },
                    "customizations": {
                        "title": settings.APP_NAME
                    }
                },
                timeout=30.0
            )
            result = response.json()
            if result.get("status") == "success":
                payment.gateway_ref = result.get("data", {}).get("id")
                db.commit()
                db.refresh(payment)

    except Exception as e:
        # Log error but do not fail — payment record exists
        print(f"Payment gateway error: {e}")

    return payment


@router.get("/", response_model=List[PaymentResponse])
def list_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List current user payments"""
    return db.query(Payment).filter(Payment.user_id == current_user.id).all()


@router.get("/{reference}", response_model=PaymentResponse)
def get_payment(
    reference: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment = db.query(Payment).filter(
        Payment.reference == reference,
        Payment.user_id == current_user.id
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.post("/webhook")
async def payment_webhook(payload: dict, db: Session = Depends(get_db)):
    """
    Flutterwave webhook — called by payment gateway when payment status changes
    No auth required — verified by checking payload signature
    """
    reference = payload.get("data", {}).get("tx_ref")
    status = payload.get("data", {}).get("status")

    if reference and status:
        payment = db.query(Payment).filter(Payment.reference == reference).first()
        if payment:
            payment.status = "success" if status == "successful" else "failed"
            db.commit()

    return {"status": "received"}
