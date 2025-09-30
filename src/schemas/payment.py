# src/schemas/payment.py
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
from datetime import datetime


class DonationBase(BaseModel):
    """Базовая схема доната"""
    amount: float
    message: Optional[str] = None
    is_anonymous: bool = False


class DonationCreate(DonationBase):
    """Схема создания доната"""
    project_id: int

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Сумма доната должна быть больше 0')
        return v


class DonationResponse(DonationBase):
    """Схема ответа доната"""
    id: int
    donor_id: int
    project_id: int
    status: str
    payment_method: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DonationWithDonorResponse(DonationResponse):
    """Донат с информацией о доноре"""
    donor: Optional['UserResponse'] = None


class TransactionBase(BaseModel):
    """Базовая схема транзакции"""
    amount: float
    currency: str = "RUB"
    transaction_type: str
    payment_provider: str


class TransactionResponse(TransactionBase):
    """Схема ответа транзакции"""
    id: int
    user_id: int
    donation_id: Optional[int]
    status: str
    provider_transaction_id: Optional[str]
    description: Optional[str]
    meta_data: Optional[Dict[str, Any]]
    wallet_address: Optional[str]
    bank_account: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class WalletBase(BaseModel):
    """Базовая схема кошелька"""
    currency: str = "RUB"
    payout_method: Optional[str] = None
    payout_threshold: float = 1000.0
    auto_payout: bool = False


class WalletResponse(WalletBase):
    """Схема ответа кошелька"""
    id: int
    user_id: int
    balance: float
    total_earned: float
    total_donated: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PayoutRequestBase(BaseModel):
    """Базовая схема запроса на вывод"""
    amount: float
    payout_method: str
    destination: str


class PayoutRequestCreate(PayoutRequestBase):
    """Схема создания запроса на вывод"""
    pass


class PayoutRequestResponse(PayoutRequestBase):
    """Схема ответа запроса на вывод"""
    id: int
    wallet_id: int
    status: str
    fee: float
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class PaymentIntentResponse(BaseModel):
    """Схема ответа платежного намерения"""
    client_secret: str
    amount: float
    currency: str
    project_id: int

from .user import UserResponse

DonationWithDonorResponse.update_forward_refs()