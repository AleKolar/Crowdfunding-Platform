# src/tests/test_repositories/test_wallets_repository.py
import pytest
from src.repository.wallets_repository import wallets_repository
from src.schemas.payment import WalletCreate


class TestWalletsRepository:
    @pytest.mark.asyncio
    async def test_create_wallet(self, db_session, test_user):
        """Тест создания кошелька"""
        wallet_data = WalletCreate(
            user_id=test_user.id,
            balance=100.0,
            total_earned=0.0,
            total_donated=0.0
        )

        wallet = await wallets_repository.create(db_session, wallet_data)
        assert wallet.id is not None
        assert wallet.user_id == test_user.id
        assert wallet.balance == 100.0

    @pytest.mark.asyncio
    async def test_get_by_user(self, db_session, test_user):
        """Тест получения кошелька пользователя"""
        wallet_data = WalletCreate(
            user_id=test_user.id,
            balance=100.0,
            total_earned=0.0,
            total_donated=0.0
        )
        await wallets_repository.create(db_session, wallet_data)

        wallet = await wallets_repository.get_by_user(db_session, test_user.id)
        assert wallet is not None
        assert wallet.user_id == test_user.id

    @pytest.mark.asyncio
    async def test_update_balance_add(self, db_session, test_user):
        """Тест увеличения баланса"""
        wallet_data = WalletCreate(
            user_id=test_user.id,
            balance=100.0,
            total_earned=0.0,
            total_donated=0.0
        )
        wallet = await wallets_repository.create(db_session, wallet_data)

        updated = await wallets_repository.update_balance(
            db_session, wallet.id, 50.0, 'add'
        )
        assert updated.balance == 150.0
        assert updated.total_earned == 50.0

    @pytest.mark.asyncio
    async def test_update_balance_subtract(self, db_session, test_user):
        """Тест уменьшения баланса"""
        wallet_data = WalletCreate(
            user_id=test_user.id,
            balance=100.0,
            total_earned=100.0,
            total_donated=0.0
        )
        wallet = await wallets_repository.create(db_session, wallet_data)

        updated = await wallets_repository.update_balance(
            db_session, wallet.id, 30.0, 'subtract'
        )
        assert updated.balance == 70.0
        assert updated.total_earned == 100.0

# pytest tests/test_repositories/test_wallets_repository.py -v --html=report.html