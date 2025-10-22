# src/services/email_service.py
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import logging
from typing import Optional
import re

from src.security.config import settings

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
        """Создание SMTP соединения"""
        try:
            context = ssl.create_default_context()

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

    def send_email(self, to_email: str, subject: str, html_content: str,
                   text_content: Optional[str] = None) -> bool:
        """СИНХРОННАЯ отправка письма"""
        try:
            # Создаем сообщение
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.smtp_from_email
            message["To"] = to_email

            if not text_content:
                text_content_clean = re.sub(r'<[^<]+?>', '', html_content)
                text_content_clean = re.sub(r'\n\s*\n', '\n', text_content_clean)
            else:
                text_content_clean = text_content

            part1 = MIMEText(text_content_clean, "plain")
            part2 = MIMEText(html_content, "html")
            message.attach(part1)
            message.attach(part2)

            # Отправляем письмо
            with self._create_smtp_connection() as server:
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)

            logger.info(f"✅ Письмо отправлено на {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка отправки письма: {e}")
            return False

    def send_welcome_email(self, to_email: str, username: str) -> bool:
        """Отправка приветственного письма"""
        try:
            from src.services.template_service import template_service

            subject = "🎉 Добро пожаловать в CrowdPlatform!"
            html_content = template_service.render_email_template(
                "welcome_email.html",
                username=username
            )

            return self.send_email(to_email, subject, html_content)

        except Exception as e:
            logger.error(f"❌ Ошибка подготовки welcome email: {e}")
            return False

    def send_verification_code_email(self, to_email: str, username: str, verification_code: str) -> bool:
        """Отправка кода подтверждения"""
        try:
            from src.services.template_service import template_service

            subject = "🔐 Код подтверждения для CrowdPlatform"
            html_content = template_service.render_email_template(
                "verification_code.html",
                username=username,
                verification_code=verification_code,
                code_expire_minutes=getattr(settings, 'SMS_CODE_EXPIRE_MINUTES', 10)
            )

            return self.send_email(to_email, subject, html_content)

        except Exception as e:
            logger.error(f"❌ Ошибка подготовки verification email: {e}")
            return False

email_service = EmailService()