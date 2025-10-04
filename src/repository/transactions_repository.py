# src/repository/transactions_repository.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.base import BaseRepository
from src.database.models import Transaction
from src.schemas.payment import TransactionCreate, TransactionUpdate


class TransactionsRepository(BaseRepository[Transaction, TransactionCreate, TransactionUpdate]):
    def __init__(self):
        super().__init__(Transaction)

    async def get_by_user(
            self,
            db: AsyncSession,
            user_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> List[Transaction]:
        return await self.get_by_field(
            db,
            field_name='user_id',
            field_value=user_id,
            order_by=Transaction.created_at.desc(),
            skip=skip,
            limit=limit
        )

    async def get_by_provider_id(
            self,
            db: AsyncSession,
            provider_transaction_id: str
    ) -> Optional[Transaction]:
        transactions = await self.get_by_field(
            db,
            field_name='provider_transaction_id',
            field_value=provider_transaction_id,
            limit=1
        )
        return transactions[0] if transactions else None

    async def update_status(
            self,
            db: AsyncSession,
            transaction_id: int,
            status: str,
            provider_transaction_id: Optional[str] = None
    ) -> Transaction:
        """Обновление статуса транзакции"""
        update_data = {'status': status}
        if provider_transaction_id:
            update_data['provider_transaction_id'] = provider_transaction_id

        transaction = await self.get(db, transaction_id)
        if transaction:
            return await self.update(db, transaction, TransactionUpdate(**update_data))
        raise ValueError(f"Transaction {transaction_id} not found")


transactions_repository = TransactionsRepository()