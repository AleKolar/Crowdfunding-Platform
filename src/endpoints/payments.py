# src/routes/payment.py
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.postgres import get_db
from src.schemas.payment import (
    PaymentIntentResponse,
    PaymentIntentCreate,
    WebhookResponse
)
from src.services.payment_service import payment_service
from src.security.auth import get_current_user


payments_router = APIRouter(
    prefix="/payments",
    tags=["payments"],
    responses={404: {"description": "Not found"}}
)

@payments_router.post("/donate", response_model=PaymentIntentResponse)
async def create_donation(
    donation_data: PaymentIntentCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание доната"""
    try:
        result = await payment_service.create_donation_intent(
            db=db,  # ← ДОБАВИЛИ сессию БД
            amount=donation_data.amount,
            project_id=donation_data.project_id,
            donor_id=current_user.id,
            currency=donation_data.currency
        )

        return PaymentIntentResponse(
            client_secret=result['client_secret'],
            payment_intent_id=result['payment_intent_id'],
            donation_id=result['donation_id'],
            amount=donation_data.amount,
            currency=donation_data.currency,
            project_id=donation_data.project_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@payments_router.post("/webhook", response_model=WebhookResponse)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Вебхук для обработки событий от Stripe"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )

    result = await payment_service.handle_webhook(db, payload, sig_header)  # ← ДОБАВИЛИ сессию
    return result


@payments_router.get("/status/{payment_intent_id}")
async def get_payment_status(payment_intent_id: str):
    """Получение статуса платежа"""
    status_info = await payment_service.get_payment_status(payment_intent_id)
    return status_info


@payments_router.post("/refund/{payment_intent_id}")
async def create_refund(
        payment_intent_id: str,
        amount: Optional[float] = None,
        current_user=Depends(get_current_user)
):
    """Создание возврата средств"""
    refund_id = await payment_service.create_refund(payment_intent_id, amount)
    return {"refund_id": refund_id, "status": "refund_created"}

# src/routes/payment.py - можно добавить позже
from src.repository.donations_repository import donations_repository

@payments_router.get("/donations/project/{project_id}")
async def get_project_donations(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Получение донатов проекта"""
    return await donations_repository.get_by_project(db, project_id, skip, limit)

@payments_router.get("/donations/my")
async def get_my_donations(
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение донатов текущего пользователя"""
    return await donations_repository.get_by_donor(db, current_user.id, skip, limit)

@payments_router.get("/donations/project/{project_id}/recent")
async def get_recent_project_donations(
    project_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Получение последних донатов проекта"""
    return await donations_repository.get_recent_donations(db, project_id, limit)