// Базовые функции для работы с API
const API_BASE = 'http://localhost:8000';

function logResult(message) {
    const results = document.getElementById('api-results');
    results.textContent += `\n${new Date().toLocaleTimeString()}: ${message}`;
    results.scrollTop = results.scrollHeight;
}

async function testAuth() {
    try {
        logResult('🔐 Тестируем аутентификацию...');

        // Тест регистрации
        const registerData = {
            email: `test_${Date.now()}@example.com`,
            phone: `+7999${Date.now().toString().slice(-7)}`,
            username: `user_${Date.now().toString().slice(-6)}`,
            password: "TestPass123!",
            secret_code: "1234"
        };

        const registerResponse = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(registerData)
        });

        if (registerResponse.ok) {
            const registerResult = await registerResponse.json();
            logResult(`✅ Регистрация успешна! User ID: ${registerResult.user_id}`);

            // Обновляем информацию о пользователе
            document.getElementById('user-id').textContent = registerResult.user_id;
            document.getElementById('user-email').textContent = registerData.email;
            document.getElementById('user-status').textContent = 'Зарегистрирован';
            document.getElementById('user-status').className = 'badge bg-success';

        } else {
            const error = await registerResponse.json();
            logResult(`❌ Ошибка регистрации: ${error.detail}`);
        }
    } catch (error) {
        logResult(`💥 Ошибка: ${error.message}`);
    }
}

async function getProjects() {
    try {
        logResult('📊 Получаем список проектов...');

        const response = await fetch(`${API_BASE}/projects/`);

        if (response.ok) {
            const projects = await response.json();
            logResult(`✅ Получено проектов: ${projects.pagination?.total || projects.length}`);
            logResult(JSON.stringify(projects, null, 2));
        } else {
            const error = await response.json();
            logResult(`❌ Ошибка получения проектов: ${error.detail}`);
        }
    } catch (error) {
        logResult(`💥 Ошибка: ${error.message}`);
    }
}

async function getWebinars() {
    try {
        logResult('🎥 Получаем список вебинаров...');

        const response = await fetch(`${API_BASE}/webinars/announcements`);

        if (response.ok) {
            const webinars = await response.json();
            logResult(`✅ Получено анонсов вебинаров: ${webinars.count}`);
            logResult(JSON.stringify(webinars, null, 2));
        } else {
            const error = await response.json();
            logResult(`❌ Ошибка получения вебинаров: ${error.detail}`);
        }
    } catch (error) {
        logResult(`💥 Ошибка: ${error.message}`);
    }
}

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    logResult('🚀 Дашборд загружен! Используйте кнопки для тестирования API.');
});