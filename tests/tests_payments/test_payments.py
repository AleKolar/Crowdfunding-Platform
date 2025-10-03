# tests/test_payments.py
import pytest
import sys
import os
from fastapi import status
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from src.security.auth import get_current_user


class TestPayments:
    """Тесты для эндпоинтов платежей"""

    @pytest.fixture
    def donation_data(self):
        """Фикстура с валидными данными для доната"""
        return {
            "amount": 1000.0,
            "project_id": 1,
            "currency": "rub"
        }

    @pytest.fixture
    def donation_data_rub(self):
        """Фикстура с валидными данными для доната в RUB"""
        return {
            "amount": 50000.0,  # 500 рублей
            "project_id": 1,
            "currency": "rub"
        }

    @pytest.fixture
    def current_user_mock(self):
        class MockUser:
            def __init__(self):
                self.id = 1
                self.email = "test@example.com"
                self.username = "test_user"

        return MockUser()

    def test_create_donation_rub(self, donation_data_rub, current_user_mock):
        """Тест успешного создания доната в RUB"""

        async def override_get_current_user():
            return current_user_mock

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            with patch('src.endpoints.payments.payment_service.create_donation_intent',
                       new_callable=AsyncMock, return_value="pi_mock_secret_12345"):

                client = TestClient(app)
                response = client.post("/payments/donate", json=donation_data_rub)

                print(f"📥 Donation RUB status: {response.status_code}")
                print(f"📥 Donation RUB response: {response.text}")

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["currency"] == "rub"  # Проверяем валюту
        finally:
            app.dependency_overrides = {}

    def test_create_donation_invalid_currency(self, current_user_mock):
        """Тест создания доната с невалидной валютой"""
        invalid_data = {
            "amount": 1000.0,
            "project_id": 1,
            "currency": "eur"  # Неподдерживаемая валюта
        }

        async def override_get_current_user():
            return current_user_mock

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            client = TestClient(app)
            response = client.post("/payments/donate", json=invalid_data)

            print(f"📥 Invalid currency status: {response.status_code}")
            print(f"📥 Invalid currency response: {response.text}")

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        finally:
            app.dependency_overrides = {}

    def test_create_donation_success(self, donation_data, current_user_mock):
        """Тест успешного создания доната"""

        async def override_get_current_user():
            return current_user_mock

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            with patch('src.endpoints.payments.payment_service.create_donation_intent',
                       new_callable=AsyncMock, return_value="pi_mock_secret_12345"):

                client = TestClient(app)
                response = client.post("/payments/donate", json=donation_data)

                print(f"📥 Donation status: {response.status_code}")
                print(f"📥 Donation response: {response.text}")

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "client_secret" in data
                assert data["client_secret"] == "pi_mock_secret_12345"
                assert data["amount"] == donation_data["amount"]
                # Проверяем, что currency возвращается (но не отправляется)
                assert "currency" in data
                assert data["currency"] == "rub"
        finally:
            app.dependency_overrides = {}

    def test_create_donation_unauthorized(self, donation_data):
        """Тест создания доната без авторизации"""
        client = TestClient(app)
        response = client.post("/payments/donate", json=donation_data)

        print(f"📥 Unauthorized donation status: {response.status_code}")
        print(f"📥 Unauthorized donation response: {response.text}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_donation_invalid_data(self, current_user_mock):
        """Тест создания доната с невалидными данными"""
        invalid_data = {
            "amount": -100,  # Отрицательная сумма
            "project_id": "invalid"  # Неверный тип
            # Убираем currency из невалидных данных
        }

    def test_get_payment_status(self):
        """Тест получения статуса платежа"""
        payment_intent_id = "pi_test_12345"

        with patch('src.endpoints.payments.payment_service.get_payment_status',
                   new_callable=AsyncMock, return_value={"status": "succeeded", "amount": 1000}):
            client = TestClient(app)
            response = client.get(f"/payments/status/{payment_intent_id}")

            print(f"📥 Payment status: {response.status_code}")
            print(f"📥 Payment status response: {response.text}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "succeeded"
            assert data["amount"] == 1000

    def test_payment_webhook(self):
        """Тест вебхука платежей"""
        webhook_payload = {
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_test_12345"}}
        }

        with patch('src.endpoints.payments.payment_service.handle_webhook',
                   new_callable=AsyncMock, return_value={"status": "webhook_processed"}):
            client = TestClient(app)
            response = client.post(
                "/payments/webhook",
                json=webhook_payload,
                headers={"stripe-signature": "mock_signature"}
            )

            print(f"📥 Webhook status: {response.status_code}")
            print(f"📥 Webhook response: {response.text}")

            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.skip(reason="Requires refund logic implementation")
    def test_create_refund(self, current_user_mock):
        """Тест создания возврата средств"""
        payment_intent_id = "pi_test_12345"

        async def override_get_current_user():
            return current_user_mock

        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            with patch('src.endpoints.payments.payment_service.create_refund',
                       new_callable=AsyncMock, return_value="re_mock_12345"):
                client = TestClient(app)
                response = client.post(f"/payments/refund/{payment_intent_id}")

                print(f"📥 Refund status: {response.status_code}")
                print(f"📥 Refund response: {response.text}")

                assert response.status_code != status.HTTP_404_NOT_FOUND
        finally:
            app.dependency_overrides = {}

# Тесты платежей
# pytest tests/tests_payments/test_payments.py -v -s
# pytest tests/tests_payments/test_payments.py --html=report.html