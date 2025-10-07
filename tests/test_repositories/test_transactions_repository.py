# src/tests/test_repositories/test_transactions_repository.py
# src/tests/test_repositories/test_transactions_repository.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.transactions_repository import transactions_repository
from src.schemas.payment import TransactionCreate, TransactionType, TransactionStatus, PaymentProvider


class TestTransactionsRepository:
    """Тесты для репозитория транзакций"""

    @pytest.mark.asyncio
    async def test_create_transaction(self, db_session: AsyncSession):
        """Тест создания транзакции"""
        transaction_data = TransactionCreate(
            user_id=1,
            amount=100.0,
            currency="USD",
            status=TransactionStatus.PENDING,  # ✅ Enum вместо строки
            transaction_type=TransactionType.DONATION,  # ✅ Enum вместо строки
            payment_provider=PaymentProvider.STRIPE  # ✅ Обязательное поле
        )

        transaction = await transactions_repository.create(db_session, transaction_data)

        assert transaction.id is not None
        assert transaction.user_id == 1
        assert transaction.amount == 100.0
        assert transaction.status == TransactionStatus.PENDING
        assert transaction.transaction_type == TransactionType.DONATION
        assert transaction.payment_provider == PaymentProvider.STRIPE

    @pytest.mark.asyncio
    async def test_get_by_user(self, db_session: AsyncSession):
        """Тест получения транзакций пользователя"""
        # Создаем несколько транзакций
        for i in range(3):
            transaction_data = TransactionCreate(
                user_id=1,
                amount=100.0 + i,
                currency="USD",
                status=TransactionStatus.COMPLETED,
                transaction_type=TransactionType.DONATION,
                payment_provider=PaymentProvider.STRIPE
            )
            await transactions_repository.create(db_session, transaction_data)

        transactions = await transactions_repository.get_by_user(db_session, user_id=1)

        assert len(transactions) == 3
        assert all(transaction.user_id == 1 for transaction in transactions)

    @pytest.mark.asyncio
    async def test_update_status(self, db_session: AsyncSession):
        """Тест обновления статуса транзакции"""
        transaction_data = TransactionCreate(
            user_id=1,
            amount=100.0,
            currency="USD",
            status=TransactionStatus.PENDING,
            transaction_type=TransactionType.DONATION,
            payment_provider=PaymentProvider.STRIPE
        )
        transaction = await transactions_repository.create(db_session, transaction_data)

        updated_transaction = await transactions_repository.update_status(
            db_session, transaction.id, TransactionStatus.COMPLETED, "provider_123"
        )

        assert updated_transaction.status == TransactionStatus.COMPLETED
        assert updated_transaction.provider_transaction_id == "provider_123"

# pytest tests/test_repositories/test_transactions_repository.py -v --html=report.html
