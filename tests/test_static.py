# Добавьте в main.py
import os

from main import app, STATIC_DIR


@app.get("/test-static")
async def test_static():
    """Тест статических файлов"""
    static_files = {
        "css/style.css": os.path.exists(os.path.join(STATIC_DIR, "css", "style.css")),
        "css/email.css": os.path.exists(os.path.join(STATIC_DIR, "css", "email.css")),
        "js/main.js": os.path.exists(os.path.join(STATIC_DIR, "js", "main.js")),
    }
    print(static_files, STATIC_DIR)
    return {
        "static_dir": STATIC_DIR,
        "files": static_files
    }

# pytest tests/test_static.py --html=report.html --self-contained-html