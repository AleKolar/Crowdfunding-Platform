FROM python:3.11-slim as builder

WORKDIR /app
# !!! Внимательно (мульти-стадийная сборка)
# Устанавливаем системные зависимости для сборки
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# Финальный образ
FROM python:3.11-slim

WORKDIR /app

# Устанавливаем только runtime зависимости
RUN apt-get update && apt-get install -y \
    # Добавьте сюда зависимости, нужные в runtime
    # например, для PostgreSQL: libpq5
    && rm -rf /var/lib/apt/lists/*

# Копируем установленные пакеты из builder стадии
COPY --from=builder /root/.local /root/.local

# Добавляем .local/bin в PATH
ENV PATH=/root/.local/bin:$PATH

# Копируем исходный код
COPY . .

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Команда запуска
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]