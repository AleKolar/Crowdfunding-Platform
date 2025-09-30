import stripe
from fastapi import HTTPException, status
from typing import Optional, Dict, Any
import logging
from src.config.settings import settings


# Настройка логирования
logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    async def create_donation_intent(self, amount: float, project_id: int, donor_id: int,
                                     currency: str = 'rub') -> str:
        """Создание платежного намерения для доната"""
        try:
            # Валидация суммы
            if amount <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Сумма доната должна быть больше 0"
                )

            # Конвертация в минимальные единицы (копейки/центы)
            amount_in_cents = int(amount * 100)

            # Создание платежного намерения в Stripe
            intent = stripe.PaymentIntent.create(
                amount=amount_in_cents,
                currency=currency,
                metadata={
                    'project_id': str(project_id),
                    'donor_id': str(donor_id),
                    'type': 'donation'
                },
                description=f"Донат для проекта #{project_id}",
                automatic_payment_methods={
                    'enabled': True,
                },
                # Дополнительные параметры для лучшего UX
                setup_future_usage='on_session' if amount > 1000 else None,  # Для крупных сумм
            )

            logger.info(
                f"Создано платежное намерение для доната: project_id={project_id}, donor_id={donor_id}, amount={amount}")

            return intent.client_secret

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

    async def handle_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Обработка вебхуков от Stripe"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )

            # Обработка различных типов событий
            if event['type'] == 'payment_intent.succeeded':
                return await self._handle_payment_success(event)
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
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")

    async def _handle_payment_success(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка успешного платежа"""
        payment_intent = event['data']['object']

        # Извлекаем метаданные
        metadata = payment_intent.get('metadata', {})
        project_id = metadata.get('project_id')
        donor_id = metadata.get('donor_id')

        if not project_id or not donor_id:
            logger.error(f"Missing metadata in payment intent: {payment_intent['id']}")
            return {'status': 'error', 'message': 'Missing metadata'}

        # Здесь будет логика сохранения доната в БД
        # await self._save_donation_to_db(...)

        logger.info(f"Payment successful: intent={payment_intent['id']}, project={project_id}, donor={donor_id}")
        return {'status': 'success', 'payment_intent': payment_intent['id']}

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
        except stripe.error.StripeError as e:
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


# Синглтон экземпляр сервиса
payment_service = PaymentService()