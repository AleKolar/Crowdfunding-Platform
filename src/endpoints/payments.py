# src/routes/payment.py
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from src.database.postgres import get_db
from src.schemas.payment import DonationCreate, PaymentIntentResponse
from src.services.payment_service import payment_service
from src.security.auth import get_current_user


payment_router = APIRouter(tags=["payment"], prefix="/payment")

@payment_router.post("/donate", response_model=PaymentIntentResponse)
async def create_donation(
        donation_data: DonationCreate,
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Создание доната"""
    client_secret = await payment_service.create_donation_intent(
        amount=donation_data.amount,
        project_id=donation_data.project_id,
        donor_id=current_user.id,
        currency=donation_data.currency
    )

    return PaymentIntentResponse(
        client_secret=client_secret,
        amount=donation_data.amount,
        currency=donation_data.currency,
        project_id=donation_data.project_id
    )


@payment_router.post("/webhook")
async def stripe_webhook(request: Request):
    """Вебхук для обработки событий от Stripe"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    result = await payment_service.handle_webhook(payload, sig_header)
    return result


@payment_router.get("/status/{payment_intent_id}")
async def get_payment_status(payment_intent_id: str):
    """Получение статуса платежа"""
    status_info = await payment_service.get_payment_status(payment_intent_id)
    return status_info


@payment_router.post("/refund/{payment_intent_id}")
async def create_refund(
        payment_intent_id: str,
        amount: Optional[float] = None,
        current_user=Depends(get_current_user)
):
    """Создание возврата средств"""
    refund_id = await payment_service.create_refund(payment_intent_id, amount)
    return {"refund_id": refund_id, "status": "refund_created"}