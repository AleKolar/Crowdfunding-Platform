# tests/check_webinar_integration.py
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def check_webinar_routes():
    """Проверяет что webinar router подключен"""
    from fastapi import FastAPI

    # Импортируем роутеры напрямую
    try:
        from src.endpoints.auth import auth_router
        from src.endpoints.payments import payments_router
        from src.endpoints.projects import projects_router
        from src.endpoints.webinars import webinar_router

        # Создаем тестовое приложение как в conftest.py
        test_app = FastAPI()
        test_app.include_router(auth_router)
        test_app.include_router(payments_router)
        test_app.include_router(projects_router)
        test_app.include_router(webinar_router)

        print("✅ Все роутеры успешно импортированы и подключены")

        # Проверяем маршруты вебинаров
        webinar_routes = []
        for route in test_app.routes:
            if hasattr(route, 'path') and '/webinars' in route.path:
                webinar_routes.append(route)

        if webinar_routes:
            print("✅ Webinar routes found:")
            for route in webinar_routes:
                methods = ', '.join(route.methods) if hasattr(route, 'methods') else 'GET'
                print(f"  {methods} {route.path}")
        else:
            print("❌ No webinar routes found")

        print(f"\n📊 Всего маршрутов: {len(test_app.routes)}")
        print(f"📊 Маршрутов вебинаров: {len(webinar_routes)}")

    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("🔍 Проверяем доступные модули...")

        # Проверим что есть в endpoints
        endpoints_dir = os.path.join(project_root, "src", "endpoints")
        if os.path.exists(endpoints_dir):
            print("📁 Файлы в src/endpoints/:")
            for file in os.listdir(endpoints_dir):
                if file.endswith('.py'):
                    print(f"  - {file}")


if __name__ == "__main__":
    check_webinar_routes()

# pytest tests/check_webinar_integration.py -v -s