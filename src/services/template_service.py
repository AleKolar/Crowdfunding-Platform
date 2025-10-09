from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
from pathlib import Path


class TemplateService:
    def __init__(self):
        # Путь к директории с шаблонами
        self.templates_dir = Path(__file__).parent.parent / "templates"

        # Создаем Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def render_email_template(self, template_name: str, **context) -> str:
        """Рендерит email шаблон"""
        template = self.env.get_template(f"emails/{template_name}")
        return template.render(**context)

    def render_web_template(self, template_name: str, **context) -> str:
        """Рендерит web шаблон"""
        template = self.env.get_template(f"web/{template_name}")
        return template.render(**context)


template_service = TemplateService()