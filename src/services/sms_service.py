import logging
from typing import Optional
import requests

# Логирование
logger = logging.getLogger(__name__)


class SMSService:
    def __init__(self):
        # В реальном приложении - настройки SMS провайдера
        self.api_key = "your-sms-provider-api-key"
        self.base_url = "https://api.sms-provider.com"

    async def send_verification_code(self, phone: str, code: str) -> bool:
        """
        Отправка SMS с кодом подтверждения
        В development режиме просто логируем
        """
        try:
            # Эмуляция отправки SMS
            message = f"Ваш код подтверждения: {code}. Не сообщайте его никому."

            # В реальном приложении:
            # response = requests.post(
            #     f"{self.base_url}/send",
            #     json={"phone": phone, "message": message},
            #     headers={"Authorization": f"Bearer {self.api_key}"}
            # )

            logger.info(f"SMS отправлено на {phone}: {code}")
            print(f"📱 SMS для {phone}: Код подтверждения - {code}")

            # Эмуляция задержки сети
            import asyncio
            await asyncio.sleep(0.5)

            return True

        except Exception as e:
            logger.error(f"Ошибка отправки SMS: {e}")
            return False


# Синглтон сервиса
sms_service = SMSService()