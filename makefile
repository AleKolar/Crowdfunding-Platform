# Makefile
.PHONY: dev build up down logs clean test shell

# Development с hot-reload (для активной разработки)
dev:
	docker-compose up --build

# Сборка без запуска
build:
	docker-compose build

# Запуск в фоне
up:
	docker-compose up -d

# Остановка контейнеров
down:
	docker-compose down

# Просмотр логов в реальном времени
logs:
	docker-compose logs -f

# Полная очистка (контейнеры, volumes, образы)
clean:
	docker-compose down -v
	docker system prune -f

# Запуск тестов (когда добавите тесты)
test:
	docker-compose exec auth-api python -m pytest

# Shell внутри контейнера с приложением (ОЧЕНЬ ПОЛЕЗНО!)
shell:
	docker-compose exec auth-api bash

# Миграции базы данных (когда добавите Alembic)
migrate:
	docker-compose exec auth-api alembic upgrade head
	# Генерация секретного ключа
generate-secret:
	@echo "Сгенерированный SECRET_KEY:"
	@python -c "import secrets; print(secrets.token_urlsafe(32))"

