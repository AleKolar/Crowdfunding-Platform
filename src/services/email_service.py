# src/services/email_service.py
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config.settings import settings
import logging
from typing import Optional
import re
import asyncio

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Настройки SMTP сервера
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_from_email = settings.SMTP_FROM_EMAIL
        self.use_ssl = settings.SMTP_USE_SSL
        self.use_tls = settings.SMTP_USE_TLS

    def _create_smtp_connection(self) -> smtplib.SMTP:
        """
        Создание безопасного SMTP соединения
        """
        try:
            context = ssl.create_default_context()
            context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
            context.minimum_version = ssl.TLSVersion.TLSv1_2

            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                if self.use_tls:
                    server.starttls(context=context)

            return server

        except Exception as e:
            logger.error(f"Ошибка создания SMTP соединения: {e}")
            raise

    async def send_email(self,
                         to_email: str,
                         subject: str,
                         html_content: str,
                         text_content: Optional[str] = None) -> bool:
        """
        Отправка письма на Email пользователя
        ВСЕГДА отправляем реальное письмо!
        """
        try:
            # Создаем сообщение
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.smtp_from_email
            message["To"] = to_email

            # Если не предоставлен текстовый контент, создаем упрощенную версию
            if not text_content:
                # Простая текстовая версия HTML контента
                text_content = re.sub('<[^<]+?>', '', html_content)  # Удаляем HTML теги
                text_content = re.sub('\n\s*\n', '\n', text_content)  # Убираем лишние переносы

            # Добавляем обе версии (текстовую и HTML)
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")

            message.attach(part1)
            message.attach(part2)

            # ВСЕГДА отправляем реальное письмо!
            with self._create_smtp_connection() as server:
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)

            logger.info(f"✅ Письмо отправлено на {to_email}: {subject}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ Ошибка аутентификации SMTP: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ Ошибка SMTP при отправке письма: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка отправки письма: {e}")
            return False

    async def send_welcome_email(self, to_email: str, username: str) -> bool:
        """
        Отправка приветственного письма
        """
        from src.services.template_service import template_service

        subject = "🎉 Добро пожаловать в CrowdPlatform!"
        html_content = template_service.render_email_template(
            "welcome.html",
            username=username,
            platform_url=settings.PLATFORM_URL
        )

        return await self.send_email(to_email, subject, html_content)

    async def send_password_reset_email(self, to_email: str, reset_token: str, username: str) -> bool:
        """
        Отправка письма для сброса пароля
        """
        from src.services.template_service import template_service

        subject = "🔐 Сброс пароля CrowdPlatform"
        reset_url = f"{settings.PLATFORM_URL}/reset-password?token={reset_token}"

        html_content = template_service.render_email_template(
            "password_reset.html",
            username=username,
            reset_url=reset_url,
            reset_token=reset_token
        )

        return await self.send_email(to_email, subject, html_content)

    async def send_verification_code_email(self, to_email: str, username: str, verification_code: str) -> bool:
        """
        Отправка кода подтверждения по email
        """
        from src.services.template_service import template_service

        subject = "🔐 Код подтверждения для CrowdPlatform"
        html_content = template_service.render_email_template(
            "verification_code.html",
            username=username,
            verification_code=verification_code,
            platform_url=settings.PLATFORM_URL
        )

        return await self.send_email(to_email, subject, html_content)

    def test_connection(self) -> bool:
        """
        Тестирование подключения к SMTP серверу
        """
        try:
            with self._create_smtp_connection() as server:
                server.login(self.smtp_username, self.smtp_password)
                logger.info("✅ SMTP соединение успешно установлено")
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования SMTP соединения: {e}")
            return False


email_service = EmailService()