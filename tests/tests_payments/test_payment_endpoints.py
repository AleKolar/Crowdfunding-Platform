# src/tests/tests_payments/test_payment_endpoints.py
import pytest
from fastapi import status
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
class TestPaymentEndpoints:
    """Тесты платежных эндпоинтов"""

    async def test_create_donation_success(self, client, current_user_mock):
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
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["client_secret"] == "cs_test_secret"
            assert data["payment_intent_id"] == "pi_test123"

    async def test_create_donation_validation_errors(self, client):
        """Тестируем разные случаи валидации - используем реальные статусы"""
        # Сначала протестируем что все эти случаи возвращают ошибки (не 200)
        test_cases = [
            ({"amount": -100, "project_id": 1, "currency": "rub"}, "negative amount"),
            ({"amount": 0, "project_id": 1, "currency": "rub"}, "zero amount"),
            ({"amount": 1000, "currency": "invalid"}, "invalid currency"),
            ({"amount": 1000, "project_id": 1}, "missing currency"),
            ({"project_id": 1, "currency": "rub"}, "missing amount"),
            ({"amount": "not_a_number", "project_id": 1, "currency": "rub"}, "string amount"),
        ]

        for data, description in test_cases:
            response = client.post("/payments/donate", json=data)
            print(f"🔍 {description}: status {response.status_code}")

            # Все эти случаи должны возвращать ошибку (не 200)
            assert response.status_code != status.HTTP_200_OK, f"Expected error for {description}"

    async def test_create_donation_with_mock_errors(self, client):
        """Тестируем бизнес-ошибки с моками"""
        # Валидные данные, но с ошибками в бизнес-логике
        valid_data = {
            "amount": 1000.0,
            "project_id": 1,
            "currency": "rub"
        }

        # Тест с ошибкой сервиса
        with patch('src.endpoints.payments.payment_service.create_donation_intent',
                   new_callable=AsyncMock) as mock_service:
            mock_service.side_effect = Exception("Payment service error")

            response = client.post("/payments/donate", json=valid_data)
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_get_payment_status_success(self, client):
        """Получение статуса платежа"""
        payment_intent_id = "pi_test123"

        with patch('src.endpoints.payments.payment_service.get_payment_status', new_callable=AsyncMock) as mock_service:
            mock_service.return_value = {
                "payment_intent_id": payment_intent_id,
                "status": "succeeded",
                "amount": 1000,
                "currency": "rub"
            }

            response = client.get(f"/payments/status/{payment_intent_id}")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert data["payment_intent_id"] == payment_intent_id
            assert data["status"] == "succeeded"

    async def test_get_payment_status_error(self, client):
        """Получение статуса несуществующего платежа"""
        payment_intent_id = "pi_nonexistent"

        with patch('src.endpoints.payments.payment_service.get_payment_status', new_callable=AsyncMock) as mock_service:
            from fastapi import HTTPException
            mock_service.side_effect = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment intent not found"
            )

            response = client.get(f"/payments/status/{payment_intent_id}")
            assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
class TestDonationHistoryEndpoints:
    """Тесты истории донатов"""

    async def test_get_project_donations(self, client):
        """Получение донатов проекта"""
        project_id = 1

        with patch('src.endpoints.payments.donations_repository.get_by_project', new_callable=AsyncMock) as mock_repo:
            mock_repo.return_value = [
                {
                    "id": 1,
                    "amount": 1000.0,
                    "currency": "RUB",
                    "status": "completed",
                    "donor_id": 1,
                    "project_id": project_id,
                    "created_at": "2023-01-01T00:00:00"
                }
            ]

            response = client.get(f"/payments/donations/project/{project_id}")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert len(data) == 1
            assert data[0]["amount"] == 1000.0

    async def test_get_my_donations(self, client, current_user_mock):
        """Получение донатов текущего пользователя"""
        with patch('src.endpoints.payments.donations_repository.get_by_donor', new_callable=AsyncMock) as mock_repo:
            mock_repo.return_value = [
                {
                    "id": 1,
                    "amount": 500.0,
                    "currency": "RUB",
                    "status": "completed",
                    "donor_id": current_user_mock.id,
                    "project_id": 1,
                    "created_at": "2023-01-01T00:00:00"
                }
            ]

            response = client.get("/payments/donations/my")
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert len(data) == 1
            assert data[0]["donor_id"] == current_user_mock.id


@pytest.mark.asyncio
class TestWebhookEndpoints:
    """Тесты вебхуков"""

    async def test_webhook_missing_signature(self, client):
        """Вебхук без подписи"""
        response = client.post("/payments/webhook", json={"type": "test"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_webhook_with_signature(self, client):
        """Вебхук с подписью"""
        with patch('src.services.payment_service.stripe.Webhook.construct_event') as mock_construct, \
                patch('src.endpoints.payments.payment_service.handle_webhook', new_callable=AsyncMock) as mock_handler:
            # Мок успешного события
            mock_event = type('obj', (), {
                'type': 'payment_intent.succeeded',
                'data': type('obj', (), {
                    'object': type('obj', (), {
                        'id': 'pi_test123',
                        'amount': 1000,
                        'currency': 'rub'
                    })()
                })()
            })()

            mock_construct.return_value = mock_event
            mock_handler.return_value = {"status": "processed"}

            response = client.post(
                "/payments/webhook",
                json={"type": "payment_intent.succeeded"},
                headers={"stripe-signature": "test_signature"}
            )

            assert response.status_code == status.HTTP_200_OK

    async def test_webhook_invalid_signature(self, client):
        """Вебхук с невалидной подписью"""
        with patch('src.services.payment_service.stripe.Webhook.construct_event') as mock_construct:
            import stripe
            try:
                error_class = stripe.SignatureVerificationError
            except AttributeError:
                error_class = stripe.error.SignatureVerificationError

            mock_construct.side_effect = error_class(
                "Invalid signature", "sig_header"
            )

            response = client.post(
                "/payments/webhook",
                json={"type": "payment_intent.succeeded"},
                headers={"stripe-signature": "invalid_signature"}
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST


# pytest tests/tests_payments/test_payment_endpoints.py --html=report.html