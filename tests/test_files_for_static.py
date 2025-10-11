# # tests/test_files_for_static.py
import os


def create_test_files():
    """Создает тестовые статические файлы"""
    static_dir = "src/static"

    # Создаем папки
    os.makedirs(f"{static_dir}/css", exist_ok=True)
    os.makedirs(f"{static_dir}/js", exist_ok=True)

    # Создаем style.css
    with open(f"{static_dir}/css/style.css", "w", encoding="utf-8") as f:
        f.write("""
/* ТЕСТОВЫЕ СТИЛИ - если работают, будет видно */
body {
    background-color: #e8f4f8 !important;
}

.navbar-brand {
    color: #ff6b6b !important;
    font-weight: bold;
}

.test-css-success {
    color: green;
    border: 3px solid green;
    padding: 15px;
    margin: 20px;
    background: #d4edda;
    font-weight: bold;
    text-align: center;
}
""")

    # Создаем email.css
    with open(f"{static_dir}/css/email.css", "w", encoding="utf-8") as f:
        f.write("""
/* Стили для email */
.email-template {
    max-width: 600px;
    margin: 0 auto;
}
""")

    # Создаем main.js
    with open(f"{static_dir}/js/main.js", "w", encoding="utf-8") as f:
        f.write("""
// ТЕСТОВЫЙ JavaScript
console.log("✅ main.js загружен успешно!");

document.addEventListener('DOMContentLoaded', function() {
    console.log("✅ DOM готов!");

    // Добавляем тестовый блок
    const testDiv = document.createElement('div');
    testDiv.className = 'test-css-success';
    testDiv.innerHTML = '🎉 CSS и JavaScript работают корректно!';
    document.body.prepend(testDiv);

    // Обновляем статус авторизации
    const authStatus = document.getElementById('authStatus');
    if (authStatus) {
        authStatus.textContent = '✅ Static files loaded';
        authStatus.style.color = 'green';
    }
});
""")

    print("✅ Тестовые файлы созданы!")


if __name__ == "__main__":
    create_test_files()

# pytest tests/test_files_for_static.py --html=report.html --self-contained-html
