// ОСНОВНОЙ JAVASCRIPT ДЛЯ ПРИЛОЖЕНИЯ
console.log("🚀 main.js загружен успешно!");

// Утилиты для работы с API
class ApiClient {
    static async request(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            const data = await response.json();
            return {
                success: response.ok,
                data: data,
                status: response.status
            };
        } catch (error) {
            console.error('API Error:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    static async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
}

// Управление уведомлениями
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.querySelector('.container').prepend(alertDiv);

    // Автоматическое скрытие через 5 секунд
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Проверка авторизации
function checkAuthStatus() {
    const authStatus = document.getElementById('authStatus');
    if (!authStatus) return;

    const token = localStorage.getItem('auth_token');

    if (token) {
        authStatus.textContent = '✅ Авторизован';
        authStatus.className = 'nav-link text-success';
    } else {
        authStatus.textContent = '❌ Не авторизован';
        authStatus.className = 'nav-link text-warning';
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log("✅ DOM загружен, инициализация...");

    checkAuthStatus();

    // Показываем тестовое уведомление
    showAlert('✅ CSS и JavaScript успешно загружены!', 'success');

    // Добавляем кнопку выхода если авторизован
    const token = localStorage.getItem('auth_token');
    if (token) {
        const navbar = document.querySelector('.navbar-nav');
        if (navbar) {
            const logoutBtn = document.createElement('a');
            logoutBtn.className = 'nav-link text-danger';
            logoutBtn.href = '#';
            logoutBtn.innerHTML = '🚪 Выход';
            logoutBtn.onclick = function(e) {
                e.preventDefault();
                localStorage.removeItem('auth_token');
                window.location.href = '/';
            };
            navbar.appendChild(logoutBtn);
        }
    }

    console.log("🎉 Инициализация завершена!");
});