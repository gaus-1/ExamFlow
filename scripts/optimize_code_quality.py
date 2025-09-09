#!/usr/bin/env python3
"""
Скрипт для улучшения качества кода
"""

import subprocess
import sys
from pathlib import Path
import re

def install_quality_tools():
    """Устанавливает инструменты качества кода"""
    print("🔧 Устанавливаем инструменты качества кода...")
    
    tools = [
        'mypy',
        'black',
        'isort',
        'flake8',
        'autoflake',
        'pylint',
        'sphinx',
        'sphinx-rtd-theme'
    ]
    
    for tool in tools:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', tool], check=True)
            print(f"✅ {tool} установлен")
        except subprocess.CalledProcessError:
            print(f"❌ Ошибка установки {tool}")

def add_type_hints():
    """Добавляет type hints в код"""
    print("📝 Добавляем type hints...")
    
    # Файлы для обработки
    files_to_process = [
        'ai/api.py',
        'core/rag_system/orchestrator.py',
        'core/rag_system/vector_store.py',
        'learning/views.py',
        'authentication/views.py'
    ]
    
    for file_path in files_to_process:
        if Path(file_path).exists():
            add_type_hints_to_file(file_path)
        else:
            print(f"⚠️ Файл {file_path} не найден")

def add_type_hints_to_file(file_path: str):
    """Добавляет type hints в конкретный файл"""
    print(f"📝 Обрабатываем {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем импорты для типов
    if 'from typing import' not in content:
        content = content.replace(
            'import os',
            'import os\nfrom typing import Dict, List, Optional, Union, Any, Tuple'
        )
    
    # Добавляем type hints к функциям
    content = add_function_type_hints(content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {file_path} обновлен")

def add_function_type_hints(content: str) -> str:
    """Добавляет type hints к функциям"""
    # Паттерн для функций без type hints
    function_pattern = r'def (\w+)\(self, ([^)]*)\):'
    
    def add_hints(match):
        func_name = match.group(1)
        _params = match.group(2)
        
        # Простые type hints для основных функций
        if func_name in ['post', 'get']:
            return f'def {func_name}(self, request: HttpRequest) -> JsonResponse:'
        elif func_name in ['process_query', 'generate_prompt']:
            return f'def {func_name}(self, query: str, user_id: Optional[int] = None) -> Dict[str, Any]:'
        elif func_name in ['create_embedding', 'search']:
            return f'def {func_name}(self, text: str, limit: int = 5) -> List[Dict[str, Any]]:'
        else:
            return match.group(0)
    
    content = re.sub(function_pattern, add_hints, content)
    return content

def add_docstrings():
    """Добавляет docstrings к функциям"""
    print("📚 Добавляем docstrings...")
    
    files_to_process = [
        'ai/api.py',
        'core/rag_system/orchestrator.py',
        'core/rag_system/vector_store.py'
    ]
    
    for file_path in files_to_process:
        if Path(file_path).exists():
            add_docstrings_to_file(file_path)

def add_docstrings_to_file(file_path: str):
    """Добавляет docstrings в файл"""
    print(f"📚 Добавляем docstrings в {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем docstrings к классам и методам
    content = add_class_docstrings(content)
    content = add_method_docstrings(content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def add_class_docstrings(content: str) -> str:
    """Добавляет docstrings к классам"""
    class_pattern = r'class (\w+)\([^)]*\):\n(?!\s*""")'
    
    def add_class_docstring(match):
        class_name = match.group(1)
        docstring = f'class {class_name}:\n    """\n    {class_name} класс\n    """\n'
        return docstring
    
    content = re.sub(class_pattern, add_class_docstring, content)
    return content

def add_method_docstrings(content: str) -> str:
    """Добавляет docstrings к методам"""
    method_pattern = r'def (\w+)\([^)]*\):\n(?!\s*""")'
    
    def add_method_docstring(match):
        method_name = match.group(1)
        docstring = f'def {method_name}():\n    """\n    {method_name} метод\n    """\n'
        return docstring
    
    content = re.sub(method_pattern, add_method_docstring, content)
    return content

def create_mypy_config():
    """Создает конфигурацию mypy"""
    print("🔍 Создаем конфигурацию mypy...")
    
    mypy_config = '''[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

[mypy-django.*]
ignore_missing_imports = True

[mypy-google.*]
ignore_missing_imports = True

[mypy-requests.*]
ignore_missing_imports = True
'''
    
    with open('mypy.ini', 'w', encoding='utf-8') as f:
        f.write(mypy_config)
    
    print("✅ Конфигурация mypy создана")

def create_black_config():
    """Создает конфигурацию Black"""
    print("🎨 Создаем конфигурацию Black...")
    
    pyproject_toml = """[tool.black]
line-length = 100
target-version = ['py311']
include = '\\.pyi?$'
extend-exclude = '''
    ^/(foo|bar)/
'''
"""
    
    with open('pyproject.toml', 'w', encoding='utf-8') as f:
        f.write(pyproject_toml)
    
    print("✅ Конфигурация Black создана")

def create_isort_config():
    """Создает конфигурацию isort"""
    print("📦 Создаем конфигурацию isort...")
    
    isort_config = '''[settings]
profile = black
line_length = 100
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
'''
    
    with open('.isort.cfg', 'w', encoding='utf-8') as f:
        f.write(isort_config)
    
    print("✅ Конфигурация isort создана")

def create_flake8_config():
    """Создает конфигурацию flake8"""
    print("🔍 Создаем конфигурацию flake8...")
    
    flake8_config = '''[flake8]
max-line-length = 100
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    .venv,
    venv,
    .env,
    migrations,
    static,
    media
'''
    
    with open('.flake8', 'w', encoding='utf-8') as f:
        f.write(flake8_config)
    
    print("✅ Конфигурация flake8 создана")

def create_documentation():
    """Создает документацию"""
    print("📚 Создаем документацию...")
    
    docs_dir = Path('docs')
    docs_dir.mkdir(exist_ok=True)
    
    # Создаем conf.py для Sphinx
    conf_py = docs_dir / 'conf.py'
    conf_content = '''"""
Конфигурация Sphinx для ExamFlow
"""

 
sys.path.insert(0, os.path.abspath('..'))

project = 'ExamFlow 2.0'
copyright = '2024, ExamFlow Team'
author = 'ExamFlow Team'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
'''
    
    with open(conf_py, 'w', encoding='utf-8') as f:
        f.write(conf_content)
    
    # Создаем index.rst
    index_rst = docs_dir / 'index.rst'
    index_content = '''ExamFlow 2.0 Documentation
============================

Добро пожаловать в документацию ExamFlow 2.0!

.. toctree::
   :maxdepth: 2
   :caption: Содержание:

   api
   modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
'''
    
    with open(index_rst, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print("✅ Документация создана")

def run_code_quality_checks():
    """Запускает проверки качества кода"""
    print("🔍 Запускаем проверки качества кода...")
    
    try:
        # Black форматирование
        subprocess.run([sys.executable, '-m', 'black', '.', '--check'], check=True)
        print("✅ Black проверка пройдена")
    except subprocess.CalledProcessError:
        print("⚠️ Black нашел проблемы форматирования")
    
    try:
        # isort проверка
        subprocess.run([sys.executable, '-m', 'isort', '.', '--check-only'], check=True)
        print("✅ isort проверка пройдена")
    except subprocess.CalledProcessError:
        print("⚠️ isort нашел проблемы с импортами")
    
    try:
        # flake8 проверка
        subprocess.run([sys.executable, '-m', 'flake8', '.'], check=True)
        print("✅ flake8 проверка пройдена")
    except subprocess.CalledProcessError:
        print("⚠️ flake8 нашел проблемы с кодом")
    
    try:
        # mypy проверка
        subprocess.run([sys.executable, '-m', 'mypy', '.'], check=True)
        print("✅ mypy проверка пройдена")
    except subprocess.CalledProcessError:
        print("⚠️ mypy нашел проблемы с типами")

def create_pre_commit_config():
    """Создает конфигурацию pre-commit"""
    print("🔄 Создаем конфигурацию pre-commit...")
    
    pre_commit_config = '''repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        args: [--line-length=100]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black]

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=100, --extend-ignore=E203,W503]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-r, ., -f, json, -o, bandit-report.json]
        exclude: ^tests/
'''
    
    with open('.pre-commit-config.yaml', 'w', encoding='utf-8') as f:
        f.write(pre_commit_config)
    
    print("✅ Конфигурация pre-commit создана")

def main():
    """Основная функция"""
    print("🚀 Начинаем улучшение качества кода...")
    
    # Устанавливаем инструменты
    install_quality_tools()
    
    # Добавляем type hints
    add_type_hints()
    
    # Добавляем docstrings
    add_docstrings()
    
    # Создаем конфигурации
    create_mypy_config()
    create_black_config()
    create_isort_config()
    create_flake8_config()
    
    # Создаем документацию
    create_documentation()
    
    # Создаем pre-commit конфигурацию
    create_pre_commit_config()
    
    # Запускаем проверки
    run_code_quality_checks()
    
    print("🎉 Улучшение качества кода завершено!")
    print("📋 Следующие шаги:")
    print("1. Установите pre-commit: pip install pre-commit")
    print("2. Установите хуки: pre-commit install")
    print("3. Запустите: pre-commit run --all-files")
    print("4. Сгенерируйте документацию: cd docs && sphinx-build -b html . _build/html")

if __name__ == "__main__":
    main()
