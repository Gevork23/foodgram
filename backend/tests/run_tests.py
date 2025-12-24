#!/usr/bin/env python
import subprocess
import sys
import os

def run_tests():
    """Запуск всех тестов"""
    # Определяем команду для pytest
    cmd = [
        sys.executable, "-m", "pytest",
        "-v",  # подробный вывод
        "--tb=short",  # короткий traceback
        "--cov=.",  # покрытие кода
        "--cov-report=term-missing",  # отчет о покрытии
        "tests/"
    ]
    
    # Запускаем тесты
    result = subprocess.run(cmd)
    return result.returncode

if __name__ == "__main__":
    # Устанавливаем переменные окружения для Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project.settings")
    
    # Импортируем Django
    import django
    django.setup()
    
    # Запускаем тесты
    sys.exit(run_tests())