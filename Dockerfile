# Dockerfile
FROM python:3.11-slim AS builder

WORKDIR /app

# Установка системных зависимостей для psycopg2 и других пакетов
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Финальный образ
FROM python:3.11-slim

WORKDIR /app

# Установка только runtime зависимостей
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование Python пакетов из builder stage
COPY --from=builder /root/.local /root/.local

# Создание non-root пользователя
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Копирование кода приложения
COPY --chown=app:app . .

# Переменные окружения
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Запуск приложения (SECRET_KEY генерируется только если не предоставлен)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]