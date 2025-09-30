import stripe
from sqlalchemy.orm import Session


class PaymentService:
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    async def create_donation_intent(self, amount: float, project_id: int, donor_id: int):
        """Создание намерения доната"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # в копейках/центах
                currency='rub',
                metadata={
                    'project_id': project_id,
                    'donor_id': donor_id
                }
            )
            return intent.client_secret
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def process_donation(self, db: Session, payment_intent_id: str):
        """Обработка успешного доната"""
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        donation = Donation(
            amount=intent.amount / 100,
            donor_id=int(intent.metadata.donor_id),
            project_id=int(intent.metadata.project_id)
        )

        db.add(donation)

        # Обновляем баланс проекта
        project = db.scalar(
            select(Project).where(Project.id == donation.project_id)
        )
        project.current_amount += donation.amount

        db.commit()