# update_readme_stats.py
import subprocess
import re
import sys


def run_tests_safely():
    """Безопасный запуск тестов с обработкой ошибок кодировки"""
    print("🚀 Запускаем тесты...")

    try:
        # Запускаем тесты без указания кодировки
        result = subprocess.run(
            ['pytest', 'tests/', '-v', '--tb=short'],
            capture_output=True,
            text=True  # text=True автоматически декодирует в UTF-8
        )

        # Безопасно объединяем stdout и stderr
        stdout = result.stdout if result.stdout else ""
        stderr = result.stderr if result.stderr else ""
        output = stdout + stderr

        return output, result.returncode

    except UnicodeDecodeError as e:
        print(f"❌ Ошибка кодировки: {e}")
        # Пробуем с другой кодировкой
        try:
            result = subprocess.run(
                ['pytest', 'tests/', '-v', '--tb=short'],
                capture_output=True
            )
            output = result.stdout.decode('cp1251', errors='ignore') + result.stderr.decode('cp1251', errors='ignore')
            return output, result.returncode
        except Exception as e2:
            print(f"❌ Критическая ошибка: {e2}")
            return f"Ошибка при запуске тестов: {e2}", 1


def parse_test_results(output):
    """Парсит результаты тестов"""
    print("📊 Анализируем результаты тестов...")

    # Ищем статистику в выводе
    passed_match = re.search(r'(\d+) passed', output)
    failed_match = re.search(r'(\d+) failed', output)
    skipped_match = re.search(r'(\d+) skipped', output)
    error_match = re.search(r'(\d+) error', output)

    stats = {
        'passed': int(passed_match.group(1)) if passed_match else 0,
        'failed': int(failed_match.group(1)) if failed_match else 0,
        'skipped': int(skipped_match.group(1)) if skipped_match else 0,
        'errors': int(error_match.group(1)) if error_match else 0,
    }

    stats['total'] = stats['passed'] + stats['failed'] + stats['skipped'] + stats['errors']
    return stats


def update_readme(stats):
    """Обновляет README.md с новой статистикой"""
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            content = f.read()

        # Обновляем статистику
        content = re.sub(
            r'\*\*Total Tests\*\* \| .* \|',
            f'**Total Tests** | {stats["total"]} |',
            content
        )

        content = re.sub(
            r'\*\*Tests Passed\*\* \| .* \|',
            f'**Tests Passed** | {stats["passed"]} ✅ |',
            content
        )

        content = re.sub(
            r'\*\*Tests Skipped\*\* \| .* \|',
            f'**Tests Skipped** | {stats["skipped"]} ⏭️ |',
            content
        )

        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        print(f"❌ Ошибка при обновлении README: {e}")
        return False


def main():
    """Основная функция"""
    try:
        # Запускаем тесты
        output, returncode = run_tests_safely()

        # Если тесты завершились с ошибкой, все равно парсим результаты
        stats = parse_test_results(output)

        # Выводим статистику
        print(f"📊 Результаты тестов:")
        print(f"   Всего тестов: {stats['total']}")
        print(f"   ✅ Пройдено: {stats['passed']}")
        print(f"   ❌ Провалено: {stats['failed']}")
        print(f"   ⏭️ Пропущено: {stats['skipped']}")
        print(f"   💥 Ошибок: {stats['errors']}")
        print(f"   Код возврата: {returncode}")

        # Обновляем README
        if update_readme(stats):
            print("✅ README.md успешно обновлен!")
        else:
            print("❌ Не удалось обновить README.md")

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Текущая статистика
# pytest tests/ --tb=short -q

# С покрытием
# pytest tests/ --cov=src --cov-report=term-missing

# С HTML отчетом
# pytest tests/ --html=report.html --self-contained-html