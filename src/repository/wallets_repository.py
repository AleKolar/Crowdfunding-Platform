# src/repository/wallets_repository.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.base import BaseRepository
from src.database.models import Wallet
from src.schemas.payment import WalletCreate, WalletUpdate


class WalletsRepository(BaseRepository[Wallet, WalletCreate, WalletUpdate]):
    def __init__(self):
        super().__init__(Wallet)

    async def get_by_user(self, db: AsyncSession, user_id: int) -> Optional[Wallet]:
        wallets = await self.get_by_field(db, 'user_id', user_id, limit=1)
        return wallets[0] if wallets else None

    async def update_balance(
            self,
            db: AsyncSession,
            wallet_id: int,
            amount: float,
            operation: str = 'add'  # 'add' или 'subtract'
    ) -> Wallet:
        """Обновление баланса кошелька"""
        wallet = await self.get(db, wallet_id)
        if not wallet:
            raise ValueError(f"Wallet {wallet_id} not found")

        if operation == 'add':
            new_balance = wallet.balance + amount
            new_total_earned = wallet.total_earned + amount
        else:
            new_balance = wallet.balance - amount
            new_total_earned = wallet.total_earned  # total_earned не уменьшаем при выводе

        update_data = {
            'balance': new_balance,
            'total_earned': new_total_earned
        }

        return await self.update(db, wallet, WalletUpdate(**update_data))

    async def increment_donated_amount(
            self,
            db: AsyncSession,
            wallet_id: int,
            amount: float
    ) -> Wallet:
        """Увеличение общей суммы пожертвований"""
        wallet = await self.get(db, wallet_id)
        if not wallet:
            raise ValueError(f"Wallet {wallet_id} not found")

        new_total_donated = wallet.total_donated + amount
        return await self.update(
            db,
            wallet,
            WalletUpdate(total_donated=new_total_donated)
        )


wallets_repository = WalletsRepository()