# src/services/payment_service.py
import stripe
from fastapi import HTTPException, status
from typing import Optional, Dict, Any
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.config.settings import settings
from src.repository.donations_repository import donations_repository
from src.repository.transactions_repository import transactions_repository
from src.repository.wallets_repository import wallets_repository
from src.repository.projects_repository import projects_repository
from src.schemas.payment import DonationCreate, TransactionCreate, TransactionUpdate, DonationUpdate, DonationStatus

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    async def create_donation_intent(
            self,
            db: AsyncSession,
            amount: float,
            project_id: int,
            donor_id: int,
            currency: str = 'rub'
    ) -> Dict[str, Any]:
        """Создание платежного намерения для доната"""
        try:
            # Валидация суммы
            if amount <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Сумма доната должна быть больше 0"
                )

            # Проверяем существование проекта
            project = await projects_repository.get(db, project_id)
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Проект не найден"
                )

            # Создаем запись о донате в БД со статусом pending
            donation_data = DonationCreate(
                project_id=project_id,
                donor_id=donor_id,
                amount=amount,
                currency=currency.upper(),
                status=DonationStatus.PENDING  # ← ИСПОЛЬЗУЕМ ENUM
            )
            donation = await donations_repository.create(db, donation_data)

            # Создаем транзакцию
            transaction_data = TransactionCreate(
                donation_id=donation.id,
                user_id=donor_id,
                amount=amount,
                currency=currency.upper(),
                transaction_type='donation',
                status='pending',
                payment_provider='stripe',
                description=f"Донат для проекта: {project.title}"
            )
            transaction = await transactions_repository.create(db, transaction_data)

            # Конвертация в минимальные единицы (копейки/центы)
            amount_in_cents = int(amount * 100)

            # Создание платежного намерения в Stripe
            intent = stripe.PaymentIntent.create(
                amount=amount_in_cents,
                currency=currency,
                metadata={
                    'project_id': str(project_id),
                    'donor_id': str(donor_id),
                    'donation_id': str(donation.id),
                    'transaction_id': str(transaction.id),
                    'type': 'donation'
                },
                description=f"Донат для проекта #{project_id}",
                automatic_payment_methods={'enabled': True},
            )

            # Обновляем транзакцию с ID платежа от Stripe
            await transactions_repository.update(
                db,
                transaction,
                TransactionUpdate(provider_transaction_id=intent.id)
            )

            logger.info(f"Создано платежное намерение: donation_id={donation.id}, intent={intent.id}")

            return {
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'donation_id': donation.id
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating donation intent: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ошибка платежной системы: {e.user_message if hasattr(e, 'user_message') else str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error creating donation intent: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Внутренняя ошибка сервера при создании платежа"
            )

    async def _save_donation_to_db(self, db: AsyncSession, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Сохранение успешного доната в БД"""
        try:
            metadata = payment_intent.get('metadata', {})
            donation_id = int(metadata.get('donation_id'))
            transaction_id = int(metadata.get('transaction_id'))
            amount = payment_intent['amount'] / 100  # Конвертируем обратно

            # Обновляем статус доната
            donation = await donations_repository.get(db, donation_id)
            if not donation:
                return {'success': False, 'error': 'Donation not found'}

            await donations_repository.update(
                db,
                donation,
                DonationUpdate(status=DonationStatus.COMPLETED)  # ← ИСПОЛЬЗУЕМ ENUM
            )

            # Обновляем статус транзакции
            transaction = await transactions_repository.get(db, transaction_id)
            if transaction:
                await transactions_repository.update(
                    db,
                    transaction,
                    TransactionUpdate(
                        status='completed',
                        completed_at=datetime.now()
                    )
                )

            # Обновляем баланс создателя проекта и статистику
            project = await projects_repository.get(db, donation.project_id)
            if project:
                # Обновляем баланс кошелька создателя
                wallet = await wallets_repository.get_by_user(db, project.creator_id)
                if wallet:
                    await wallets_repository.update_balance(db, wallet.id, amount, 'add')
                    # Увеличиваем общую сумму пожертвований пользователя
                    await wallets_repository.increment_donated_amount(db, wallet.id, amount)

                # ОБНОВЛЯЕМ СТАТИСТИКУ ДОНАТОВ ПРОЕКТА ← ДОБАВЛЕНО!
                await projects_repository.update_donation_stats(
                    db,
                    project_id=donation.project_id,
                    amount=amount
                )

            logger.info(f"Donation saved to DB: donation_id={donation_id}, amount={amount}")
            return {'success': True, 'donation_id': donation_id}

        except Exception as e:
            logger.error(f"Error saving donation to DB: {e}")
            return {'success': False, 'error': str(e)}

    async def _handle_payment_success(self, db: AsyncSession, event: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка успешного платежа"""
        payment_intent = event['data']['object']

        # Сохраняем донат в БД
        result = await self._save_donation_to_db(db, payment_intent)

        if result['success']:
            logger.info(f"Payment successful: intent={payment_intent['id']}")
            return {
                'status': 'success',
                'payment_intent': payment_intent['id'],
                'donation_id': result['donation_id']
            }
        else:
            logger.error(f"Failed to save donation: {result['error']}")
            return {
                'status': 'error',
                'payment_intent': payment_intent['id'],
                'error': result['error']
            }

    async def handle_webhook(self, db: AsyncSession, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Обработка вебхуков от Stripe с передачей сессии БД"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )

            # Обработка различных типов событий
            if event['type'] == 'payment_intent.succeeded':
                return await self._handle_payment_success(db, event)
            elif event['type'] == 'payment_intent.payment_failed':
                return await self._handle_payment_failure(event)
            elif event['type'] == 'payment_intent.canceled':
                return await self._handle_payment_cancellation(event)
            else:
                logger.info(f"Unhandled event type: {event['type']}")
                return {'status': 'unhandled'}

        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe._error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")

    async def _handle_payment_failure(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка неудачного платежа"""
        payment_intent = event['data']['object']
        logger.warning(
            f"Payment failed: {payment_intent['id']}, reason: {payment_intent.get('last_payment_error', {}).get('message', 'Unknown')}")
        return {'status': 'failed', 'payment_intent': payment_intent['id']}

    async def _handle_payment_cancellation(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка отмены платежа"""
        payment_intent = event['data']['object']
        logger.info(f"Payment canceled: {payment_intent['id']}")
        return {'status': 'canceled', 'payment_intent': payment_intent['id']}

    async def get_payment_status(self, payment_intent_id: str) -> Dict[str, Any]:
        """Получение статуса платежа"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                'status': intent.status,
                'amount': intent.amount / 100,  # Конвертируем обратно
                'currency': intent.currency,
                'created': intent.created,
                'metadata': intent.metadata
            }
        except stripe._error.StripeError as e:
            logger.error(f"Error retrieving payment intent: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ошибка при получении статуса платежа: {e}"
            )

    async def create_refund(self, payment_intent_id: str, amount: Optional[float] = None) -> str:
        """Создание возврата средств"""
        try:
            refund_params = {'payment_intent': payment_intent_id}
            if amount:
                refund_params['amount'] = int(amount * 100)

            refund = stripe.Refund.create(**refund_params)
            logger.info(f"Refund created: {refund.id}")
            return refund.id

        except stripe.error.StripeError as e:
            logger.error(f"Error creating refund: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ошибка при создании возврата: {e}"
            )


payment_service = PaymentService()