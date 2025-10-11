# run_dev.py
import uvicorn
import subprocess
import sys
import signal
import os
import socket
import time
import asyncio
from src.database.postgres import create_tables, engine
from src.database.redis_client import redis_manager


def check_redis_running():
    """Проверяет, запущен ли Redis на localhost:6379"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 6379))
        sock.close()
        return result == 0
    except:
        return False


def start_redis():
    """Запускает Redis в Docker контейнере"""
    print("🔴 Проверка Redis...")

    if check_redis_running():
        print("✅ Redis уже запущен")
        return None

    print("🚀 Запуск Redis в Docker...")
    try:
        redis_container = subprocess.Popen([
            "docker", "run", "-d", "--name", "redis-crowdfunding",
            "-p", "6379:6379", "redis:7-alpine"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Ждем запуска Redis
        time.sleep(3)

        if check_redis_running():
            print("✅ Redis успешно запущен в Docker")
            return redis_container
        else:
            print("❌ Не удалось запустить Redis")
            return None

    except Exception as e:
        print(f"❌ Ошибка запуска Redis: {e}")
        print("💡 Убедитесь, что Docker установлен и запущен")
        return None


async def init_database():
    """Инициализация базы данных и создание таблиц"""
    print("🐘 Инициализация базы данных...")

    try:
        # Создание таблиц (только для разработки)
        print("🔄 Создание таблиц БД...")
        await create_tables()  # ❌ Только для разработки !!!
        print("✅ Таблицы созданы (development mode)")

        # Инициализация Redis
        print("🔄 Инициализация Redis...")
        await redis_manager.init_redis()
        print("✅ Redis подключен успешно")

        print("✅ Все системы инициализированы")
        return True

    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        return False


def main():
    print("🚀 ПОЛНЫЙ ЗАПУСК ДЛЯ РАЗРАБОТКИ")
    print("=" * 50)
    print("🌐 Доступно по: http://localhost:8000")
    print("📚 Документация: http://localhost:8000/docs")
    print("🔧 Режим: development (авто-создание таблиц)")
    print("⏹️  Остановка: Ctrl+C")
    print("=" * 50)

    # Устанавливаем режим разработки
    os.environ["ENVIRONMENT"] = "development"

    # Запускаем Redis
    redis_container = start_redis()
    if not redis_container and not check_redis_running():
        print("❌ Redis не запущен! Приложение может работать некорректно")
        print("💡 Запустите вручную: docker run -d --name redis-crowdfunding -p 6379:6379 redis:7-alpine")

    # Запускаем Celery Worker
    print("🟢 Запуск Celery Worker...")
    celery_worker = subprocess.Popen([
        sys.executable, "-m", "celery",
        "-A", "src.tasks.celery_app",
        "worker",
        "--loglevel=info",
        "--pool=solo"
    ])

    # Запускаем Celery Beat
    print("⏰ Запуск Celery Beat...")
    celery_beat = subprocess.Popen([
        sys.executable, "-m", "celery",
        "-A", "src.tasks.celery_app",
        "beat",
        "--loglevel=info"
    ])

    def cleanup():
        print("\n🛑 Остановка сервисов...")

        # Останавливаем Redis контейнер если мы его запускали
        if redis_container:
            print("🔴 Остановка Redis контейнера...")
            subprocess.run(["docker", "stop", "redis-crowdfunding"], capture_output=True)
            subprocess.run(["docker", "rm", "redis-crowdfunding"], capture_output=True)

        celery_worker.terminate()
        celery_beat.terminate()
        print("✅ Все сервисы остановлены")

    # Обработчик сигналов для graceful shutdown
    def signal_handler(sig, frame):
        print(f"\n📞 Получен сигнал {sig}, завершаем работу...")
        cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Инициализируем базу данных (асинхронно)
        print("\n🎯 Инициализация приложения...")
        init_success = asyncio.run(init_database())

        if not init_success:
            print("❌ Ошибка инициализации. Запуск невозможен.")
            cleanup()
            return

        # Запускаем FastAPI
        print("\n🎯 Запуск FastAPI сервера...")
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            reload_dirs=["src"],
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Получена команда остановки...")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup()


if __name__ == "__main__":
    main()

# python run_dev.py