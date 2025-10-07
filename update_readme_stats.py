# update_readme_stats.py
import re
import subprocess

def main():
    print("🚀 Получаем статистику тестов для CI...")

    # Запускаем тесты
    result = subprocess.run(
        ['pytest', 'tests/', '-v', '--tb=short'],
        capture_output=True,
        text=True
    )

    output = result.stdout
    print(f"📄 Вывод тестов: {output[-500:]}")  # Последние 500 символов

    # Парсим результаты
    passed = re.search(r'(\d+) passed', output)
    failed = re.search(r'(\d+) failed', output)
    skipped = re.search(r'(\d+) skipped', output)

    stats = {
        'passed': int(passed.group(1)) if passed else 0,
        'failed': int(failed.group(1)) if failed else 0,
        'skipped': int(skipped.group(1)) if skipped else 0,
    }
    stats['total'] = stats['passed'] + stats['failed'] + stats['skipped']

    print(f"📊 Статистика: {stats}")

    # Обновляем README
    with open('README.md', 'r') as f:
        content = f.read()

    # Простые строки без f-strings для избежания проблем с экранированием
    content = re.sub(
        r'\*\*Total Tests\*\* \| .* \|',
        '**Total Tests** | ' + str(stats['total']) + ' |',
        content
    )

    content = re.sub(
        r'\*\*Tests Passed\*\* \| .* \|',
        '**Tests Passed** | ' + str(stats['passed']) + ' ✅ |',
        content
    )

    content = re.sub(
        r'\*\*Tests Skipped\*\* \| .* \|',
        '**Tests Skipped** | ' + str(stats['skipped']) + ' ⏭️ |',
        content
    )

    with open('README.md', 'w') as f:
        f.write(content)

    print(f"✅ README обновлен: {stats['passed']} passed, {stats['failed']} failed, {stats['skipped']} skipped")


if __name__ == "__main__":
    main()

# Текущая статистика
# pytest tests/ --tb=short -q

# С покрытием
# pytest tests/ --cov=src --cov-report=term-missing

# С HTML отчетом
# pytest tests/ --html=report.html --self-contained-html