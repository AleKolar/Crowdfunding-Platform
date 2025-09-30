# src/database/models/payment_models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Donation(Base):
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    donor_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    message = Column(Text, nullable=True)
    is_anonymous = Column(Boolean, default=False)
    status = Column(String, default="completed")  # pending, completed, failed, refunded
    payment_method = Column(String, default="card")  # card, wallet, crypto
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    donor = relationship("User", back_populates="donations")
    project = relationship("Project", back_populates="donations")
    transaction = relationship("Transaction", back_populates="donation", uselist=False)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    donation_id = Column(Integer, ForeignKey("donations.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    currency = Column(String, default="RUB")
    transaction_type = Column(String)  # donation, withdrawal, refund, bonus
    status = Column(String, default="pending")  # pending, completed, failed
    payment_provider = Column(String)  # stripe, yookassa, tinkoff
    provider_transaction_id = Column(String, nullable=True)  # ID транзакции в платежной системе
    description = Column(Text, nullable=True)
    metadata = Column(JSON)  # Дополнительные данные платежа

    # Для выводов средств
    wallet_address = Column(String, nullable=True)
    bank_account = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Связи
    donation = relationship("Donation", back_populates="transaction")
    user = relationship("User")


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    balance = Column(Float, default=0.0)
    total_earned = Column(Float, default=0.0)
    total_donated = Column(Float, default=0.0)
    currency = Column(String, default="RUB")

    # Настройки выплат
    payout_method = Column(String, nullable=True)  # card, bank_account, crypto
    payout_threshold = Column(Float, default=1000.0)  # Минимальная сумма для вывода
    auto_payout = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")


class PayoutRequest(Base):
    __tablename__ = "payout_requests"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"))
    amount = Column(Float)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    payout_method = Column(String)
    destination = Column(String)  # номер карты, счет, кошелек
    fee = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    wallet = relationship("Wallet")