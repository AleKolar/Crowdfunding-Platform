import importlib
from pathlib import Path

__all__ = []

# Получаем все файлы .py в директории репозиториев
repo_files = Path(__file__).parent.glob("*.py")

for repo_file in repo_files:
    if repo_file.name not in ["__init__.py", "base.py"] and not repo_file.name.startswith("_"):
        module_name = repo_file.stem
        try:
            module = importlib.import_module(f".{module_name}", package=__name__)

            # Ищем экземпляры репозиториев (обычно заканчиваются на _repository)
            for attr_name in dir(module):
                if attr_name.endswith('_repository') and not attr_name.startswith('_'):
                    repository_instance = getattr(module, attr_name)
                    globals()[attr_name] = repository_instance
                    __all__.append(attr_name)

        except ImportError as e:
            print(f"Warning: Could not import {module_name}: {e}")