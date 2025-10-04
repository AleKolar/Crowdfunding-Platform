# src/repository/donations_repository.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.repository.base import BaseRepository
from src.database.models import Donation
from src.schemas.payment import DonationCreate, DonationUpdate, DonationStatus


class DonationsRepository(BaseRepository[Donation, DonationCreate, DonationUpdate]):
    def __init__(self):
        super().__init__(Donation)

    async def get_by_project(
            self,
            db: AsyncSession,
            project_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> List[Donation]:
        """Получение донатов проекта с пагинацией"""
        return await self.get_by_field(
            db,
            field_name='project_id',
            field_value=project_id,
            order_by=Donation.created_at.desc(),
            skip=skip,
            limit=limit
        )

    async def get_by_donor(
            self,
            db: AsyncSession,
            donor_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> List[Donation]:
        """Получение донатов пользователя с пагинацией"""
        return await self.get_by_field(
            db,
            field_name='donor_id',
            field_value=donor_id,
            order_by=Donation.created_at.desc(),
            skip=skip,
            limit=limit
        )

    async def get_project_donors_count(self, db: AsyncSession, project_id: int) -> int:
        """Получение количества уникальных доноров проекта"""
        stmt = select(func.count(func.distinct(Donation.donor_id))).where(
            Donation.project_id == project_id,
            Donation.status == DonationStatus.COMPLETED
        )
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def get_recent_donations(
            self,
            db: AsyncSession,
            project_id: Optional[int] = None,
            limit: int = 10
    ) -> List[Donation]:
        """Получение последних донатов (всех или по проекту)"""
        stmt = select(Donation).where(Donation.status == DonationStatus.COMPLETED)

        if project_id:
            stmt = stmt.where(Donation.project_id == project_id)

        stmt = stmt.order_by(Donation.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_largest_donations(
            self,
            db: AsyncSession,
            project_id: Optional[int] = None,
            limit: int = 10
    ) -> List[Donation]:
        """Получение крупнейших донатов"""
        stmt = select(Donation).where(Donation.status == DonationStatus.COMPLETED)

        if project_id:
            stmt = stmt.where(Donation.project_id == project_id)

        stmt = stmt.order_by(Donation.amount.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()


donations_repository = DonationsRepository()