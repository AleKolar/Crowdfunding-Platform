# logging_config.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging():
    # Создаем папку для логов если её нет
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Настройка файлового логгера
    file_handler = RotatingFileHandler(
        filename="logs/app.log",
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )

    # Форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)

    # Настройка корневого логгера
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[file_handler, logging.StreamHandler()]
    )

    return logging.getLogger("crowdfunding")