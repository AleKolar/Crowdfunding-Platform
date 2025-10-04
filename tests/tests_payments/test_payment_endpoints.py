# src/tests/tests_payments/test_payment_endpoints.py
from fastapi import status
from unittest.mock import patch, AsyncMock


class TestPaymentEndpoints:
    """Тесты платежных эндпоинтов"""

    def test_create_donation_success(self, client, current_user_mock):
        """Успешное создание доната"""
        donation_data = {
            "amount": 1000.0,
            "project_id": 1,
            "currency": "rub"
        }

        with patch('src.endpoints.payments.payment_service.create_donation_intent',
                   new_callable=AsyncMock) as mock_service:
            mock_service.return_value = {
                'client_secret': 'cs_test_secret',
                'payment_intent_id': 'pi_test123',
                'donation_id': 1
            }

            response = client.post("/payments/donate", json=donation_data)

            print(f"📥 Create donation status: {response.status_code}")
            print(f"📥 Response: {response.text}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "client_secret" in data
            assert "payment_intent_id" in data
            assert "donation_id" in data

    def test_create_donation_invalid_amount(self, client):
        """Создание доната с невалидной суммой"""
        donation_data = {
            "amount": -100.0,
            "project_id": 1,
            "currency": "rub"
        }

        response = client.post("/payments/donate", json=donation_data)

        print(f"📥 Invalid amount status: {response.status_code}")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_donation_project_not_found(self, client):
        """Создание доната для несуществующего проекта"""
        donation_data = {
            "amount": 1000.0,
            "project_id": 999,
            "currency": "rub"
        }

        with patch('src.endpoints.payments.payment_service.create_donation_intent',
                   new_callable=AsyncMock) as mock_service:
            from fastapi import HTTPException
            mock_service.side_effect = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Проект не найден"
            )

            response = client.post("/payments/donate", json=donation_data)

            print(f"📥 Project not found status: {response.status_code}")

            assert response.status_code == status.HTTP_400_BAD_REQUEST ### !!!


class TestDonationHistoryEndpoints:
    """Тесты эндпоинтов истории донатов"""

    def test_get_project_donations(self, client):
        """Получение донатов проекта"""
        project_id = 1

        with patch('src.repository.donations_repository.donations_repository.get_by_project',
                   new_callable=AsyncMock) as mock_get:
            class MockDonation:
                def __init__(self, id, amount, currency, status, created_at, donor_id, project_id):
                    self.id = id
                    self.amount = amount
                    self.currency = currency
                    self.status = status
                    self.created_at = created_at
                    self.donor_id = donor_id
                    self.project_id = project_id

            mock_get.return_value = [
                MockDonation(1, 1000.0, "RUB", "completed", "2023-01-01T00:00:00", 1, project_id),
                MockDonation(2, 500.0, "RUB", "completed", "2023-01-02T00:00:00", 2, project_id)
            ]

            response = client.get(f"/payments/donations/project/{project_id}")

            print(f"📥 Project donations status: {response.status_code}")
            print(f"📥 Response: {response.text}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 2
            assert data[0]["amount"] == 1000.0
            assert data[1]["amount"] == 500.0

    def test_get_my_donations(self, client, current_user_mock):
        """Получение донатов текущего пользователя"""
        with patch('src.repository.donations_repository.donations_repository.get_by_donor',
                   new_callable=AsyncMock) as mock_get:
            class MockDonation:
                def __init__(self, id, amount, currency, status, created_at, donor_id, project_id):
                    self.id = id
                    self.amount = amount
                    self.currency = currency
                    self.status = status
                    self.created_at = created_at
                    self.donor_id = donor_id
                    self.project_id = project_id

            mock_get.return_value = [
                MockDonation(1, 1000.0, "RUB", "completed", "2023-01-01T00:00:00", current_user_mock.id, 1)
            ]

            response = client.get("/payments/donations/my")

            print(f"📥 My donations status: {response.status_code}")
            print(f"📥 Response: {response.text}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1
            assert data[0]["donor_id"] == current_user_mock.id


class TestWebhookEndpoints:
    """Тесты вебхук эндпоинтов"""

    def test_webhook_invalid_signature(self, client):
        """Вебхук с невалидной подписью"""
        with patch('src.services.payment_service.stripe.Webhook.construct_event') as mock_construct:
            # Универсальный импорт для всех версий Stripe
            import stripe
            try:
                # Для новых версий Stripe
                SignatureVerificationError = stripe.SignatureVerificationError
            except AttributeError:
                # Для старых версий Stripe
                SignatureVerificationError = stripe.error.SignatureVerificationError

            mock_construct.side_effect = SignatureVerificationError(
                "Invalid signature", "sig_header"
            )

            response = client.post(
                "/payments/webhook",
                data=b"test payload",
                headers={"stripe-signature": "invalid_signature"}
            )

            print(f"📥 Invalid signature status: {response.status_code}")

            assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestPaymentErrorScenarios:
    """Тесты сценариев ошибок платежей"""

    def test_payment_status_not_found(self, client):
        """Получение статуса несуществующего платежа"""
        payment_intent_id = "pi_nonexistent"

        with patch('src.services.payment_service.stripe.PaymentIntent.retrieve') as mock_retrieve:
            import stripe
            try:
                StripeError = stripe.StripeError
            except AttributeError:
                # !!! Для старых версий Stripe
                StripeError = stripe.error.StripeError

            mock_retrieve.side_effect = StripeError("Payment intent not found")

            response = client.get(f"/payments/status/{payment_intent_id}")

            print(f"📥 Payment not found status: {response.status_code}")

            assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestAdditionalPaymentEndpoints:
    """Дополнительные тесты платежных эндпоинтов"""

    def test_get_recent_project_donations(self, client):
        """Получение последних донатов проекта"""
        project_id = 1

        with patch('src.repository.donations_repository.donations_repository.get_recent_donations',
                   new_callable=AsyncMock) as mock_get:
            class MockDonation:
                def __init__(self, id, amount, currency, status, created_at, donor_id, project_id):
                    self.id = id
                    self.amount = amount
                    self.currency = currency
                    self.status = status
                    self.created_at = created_at
                    self.donor_id = donor_id
                    self.project_id = project_id

            mock_get.return_value = [
                MockDonation(1, 1000.0, "RUB", "completed", "2023-01-01T00:00:00", 1, project_id)
            ]

            response = client.get(f"/payments/donations/project/{project_id}/recent")

            print(f"📥 Recent donations status: {response.status_code}")
            print(f"📥 Response: {response.text}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1
            assert data[0]["amount"] == 1000.0

    def test_create_refund_success(self, client, current_user_mock):
        """Успешное создание возврата"""
        payment_intent_id = "pi_test123"

        with patch('src.endpoints.payments.payment_service.create_refund',
                   new_callable=AsyncMock) as mock_service:
            mock_service.return_value = "re_test123"

            response = client.post(f"/payments/refund/{payment_intent_id}")

            print(f"📥 Refund status: {response.status_code}")
            print(f"📥 Response: {response.text}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "refund_id" in data
            assert data["status"] == "refund_created"

    def test_create_refund_with_amount(self, client, current_user_mock):
        """Создание частичного возврата"""
        payment_intent_id = "pi_test123"

        with patch('src.endpoints.payments.payment_service.create_refund',
                   new_callable=AsyncMock) as mock_service:
            mock_service.return_value = "re_test123"

            response = client.post(
                f"/payments/refund/{payment_intent_id}",
                params={"amount": 500.0}
            )

            print(f"📥 Partial refund status: {response.status_code}")
            print(f"📥 Response: {response.text}")

            assert response.status_code == status.HTTP_200_OK

# pytest tests/tests_payments/test_payment_endpoints.py --html=report.html