# src/services/template_service.py
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class TemplateService:
    def __init__(self):
        # Путь к директории с шаблонами
        self.templates_dir = Path(__file__).parent.parent / "templates"

        logger.info(f"📁 Templates directory: {self.templates_dir}")

        # Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def render_email_template(self, template_name: str, **context) -> str:
        """Рендерит email шаблон"""
        try:
            logger.info(f"🎨 Rendering email template: {template_name}")
            template_path = f"emails/{template_name}"
            template = self.env.get_template(template_path)
            result = template.render(**context)
            logger.info(f"✅ Template rendered successfully: {template_name}")
            return result
        except TemplateNotFound as e:
            logger.error(f"❌ Template not found: {template_name} - {e}")
            # HTML: Запасной вариант
            return self._get_fallback_template(template_name, context)
        except Exception as e:
            logger.error(f"❌ Error rendering template {template_name}: {e}")
            return self._get_fallback_template(template_name, context)

    def _get_fallback_template(self, template_name: str, context: dict) -> str:
        """Запасной шаблон при ошибке"""
        if "welcome_email" in template_name:
            return f"""
            <html>
            <body>
                <h1>🎉 Добро пожаловать в CrowdPlatform!</h1>
                <p>Здравствуйте, {context.get('username', 'пользователь')}!</p>
                <p>Мы рады приветствовать вас в нашем сообществе!</p>
                <p>С уважением,<br>Команда CrowdPlatform</p>
            </body>
            </html>
            """
        elif "verification_code" in template_name:
            return f"""
            <html>
            <body>
                <h1>🔐 Код подтверждения</h1>
                <p>Здравствуйте, {context.get('username', 'пользователь')}!</p>
                <p>Ваш код подтверждения: <strong>{context.get('verification_code', '')}</strong></p>
                <p>Код действителен {context.get('code_expire_minutes', 10)} минут.</p>
                <p><strong>Никому не сообщайте этот код!</strong></p>
            </body>
            </html>
            """
        else:
            return f"<html><body><h1>Email от CrowdPlatform</h1><p>Данные: {context}</p></body></html>"


template_service = TemplateService()