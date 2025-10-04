# src/schemas/payment.py
from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class DonationStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class TransactionType(str, Enum):
    DONATION = "donation"
    WITHDRAWAL = "withdrawal"
    REFUND = "refund"
    BONUS = "bonus"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class PaymentProvider(str, Enum):
    STRIPE = "stripe"
    YOOKASSA = "yookassa"
    TINKOFF = "tinkoff"


# Donation Schemas
class DonationBase(BaseModel):
    """Базовая схема доната"""
    amount: float
    message: Optional[str] = None
    is_anonymous: bool = False


class DonationCreate(DonationBase):
    """Схема создания доната для репозитория"""
    project_id: int
    donor_id: int
    currency: Literal["USD", "RUB"] = "RUB"
    status: DonationStatus = DonationStatus.PENDING

    @field_validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Сумма доната должна быть больше 0')
        return v


class DonationUpdate(BaseModel):
    """Схема обновления доната для репозитория"""
    status: Optional[DonationStatus] = None
    message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DonationResponse(DonationBase):
    """Схема ответа доната"""
    id: int
    donor_id: int
    project_id: int
    status: str
    currency: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DonationWithDonorResponse(DonationResponse):
    """Донат с информацией о доноре"""
    donor: Optional['UserResponse'] = None


# Transaction Schemas
class TransactionBase(BaseModel):
    """Базовая схема транзакции"""
    amount: float
    currency: str = "RUB"
    transaction_type: TransactionType
    payment_provider: PaymentProvider


class TransactionCreate(BaseModel):
    """Схема создания транзакции для репозитория"""
    donation_id: Optional[int] = None
    user_id: int
    amount: float
    currency: str = "RUB"
    transaction_type: TransactionType
    status: TransactionStatus = TransactionStatus.PENDING
    payment_provider: PaymentProvider
    provider_transaction_id: Optional[str] = None
    description: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None


class TransactionUpdate(BaseModel):
    """Схема обновления транзакции для репозитория"""
    status: Optional[TransactionStatus] = None
    provider_transaction_id: Optional[str] = None
    completed_at: Optional[datetime] = None
    meta_data: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


# Wallet Schemas
class WalletBase(BaseModel):
    """Базовая схема кошелька"""
    currency: str = "RUB"
    payout_method: Optional[str] = None
    payout_threshold: float = 1000.0
    auto_payout: bool = False


class WalletCreate(BaseModel):
    """Схема создания кошелька для репозитория"""
    user_id: int
    balance: float = 0.0
    total_earned: float = 0.0
    total_donated: float = 0.0
    currency: str = "RUB"


class WalletUpdate(BaseModel):
    """Схема обновления кошелька для репозитория"""
    balance: Optional[float] = None
    total_earned: Optional[float] = None
    total_donated: Optional[float] = None
    payout_method: Optional[str] = None
    payout_threshold: Optional[float] = None
    auto_payout: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class WalletResponse(WalletBase):
    """Схема ответа кошелька"""
    id: int
    user_id: int
    balance: float
    total_earned: float
    total_donated: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Payout Request Schemas
class PayoutRequestBase(BaseModel):
    """Базовая схема запроса на вывод"""
    amount: float
    payout_method: str
    destination: str


class PayoutRequestCreate(BaseModel):
    """Схема создания запроса на вывод для репозитория"""
    wallet_id: int
    amount: float
    payout_method: str
    destination: str
    status: str = "pending"
    fee: float = 0.0


class PayoutRequestUpdate(BaseModel):
    """Схема обновления запроса на вывод для репозитория"""
    status: Optional[str] = None
    fee: Optional[float] = None
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PayoutRequestResponse(PayoutRequestBase):
    """Схема ответа запроса на вывод"""
    id: int
    wallet_id: int
    status: str
    fee: float
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# Payment Intent Schemas
class PaymentIntentCreate(BaseModel):
    """Схема создания платежного намерения"""
    amount: float
    project_id: int
    currency: Literal["usd", "rub"] = "rub"

    @field_validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Сумма должна быть больше 0')
        return v


class PaymentIntentResponse(BaseModel):
    """Схема ответа платежного намерения"""
    client_secret: str
    payment_intent_id: str
    donation_id: int
    amount: float
    currency: str
    project_id: int


class WebhookResponse(BaseModel):
    """Схема ответа вебхука"""
    status: str
    payment_intent: Optional[str] = None
    donation_id: Optional[int] = None
    error: Optional[str] = None


# Statistics Schemas
class DonationStatsResponse(BaseModel):
    """Статистика донатов"""
    total_donations: float
    total_donors: int
    average_donation: float
    project_total: Optional[float] = None
    donor_total: Optional[float] = None


class WalletStatsResponse(BaseModel):
    """Статистика кошелька"""
    balance: float
    total_earned: float
    total_donated: float
    available_for_payout: float


# Import в конце для избежания circular imports
from .user import UserResponse

DonationWithDonorResponse.model_rebuild()