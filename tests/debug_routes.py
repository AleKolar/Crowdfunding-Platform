# tests/debug_routes.py
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print(f"🔧 Project root: {project_root}")
print(f"🔧 Python path: {sys.path}")

try:
    from fastapi import FastAPI
    from src.endpoints.webinars import webinar_router
    app = FastAPI()
    app.include_router(webinar_router)

    print("✅ Successfully imported webinar_router")
    print("📋 Registered webinar routes:")

    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"  {route.methods} {route.path}")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("🔍 Available modules:")

    # Проверим что есть в src/
    src_path = os.path.join(project_root, "src")
    if os.path.exists(src_path):
        print("📁 Contents of src/:")
        for item in os.listdir(src_path):
            print(f"  - {item}")

        # Проверим api endpoints
        api_path = os.path.join(src_path, "api")
        if os.path.exists(api_path):
            print("📁 Contents of src/api/:")
            for item in os.listdir(api_path):
                print(f"  - {item}")

# pytest tests/debug_router.py -v -s