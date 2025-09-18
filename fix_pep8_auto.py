#!/usr/bin/env python3
"""
Автоматическое исправление основных ошибок PEP8
"""

import os
import re


def fix_pep8_file(file_path):
    """Исправляет основные ошибки PEP8 в файле"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 1. Удаляем trailing whitespace
        content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)

        # 2. Удаляем пустые строки с пробелами
        content = re.sub(r'^\s+$', '', content, flags=re.MULTILINE)

        # 3. Исправляем f-strings без placeholders
        content = re.sub(r'f"([^"]*)"', r'"\1"', content)
        content = re.sub(r"f'([^']*)'", r"'\1'", content)

        # 4. Добавляем пробелы после запятых
        content = re.sub(r',([^\s])', r', \1', content)

        # 5. Исправляем отступы для продолжения строк
        lines = content.split('\n')
        fixed_lines = []

        for i, line in enumerate(lines):
            # Исправляем отступы для продолжения строк
            if line.strip().startswith(('(', '[', '{')):
                continue
            elif line.strip() and not line.startswith((' ', '\t')) and i > 0:
                prev_line = lines[i-1].strip()
                if prev_line.endswith(('(', '[', '{', ',')):
                    # Это продолжение строки, нужно добавить отступ
                    if '=' in prev_line and not prev_line.endswith('='):
                        # Присваивание
                        indent = ' ' * 8
                    else:
                        # Обычное продолжение
                        indent = ' ' * 4
                    line = indent + line.strip()

            fixed_lines.append(line)

        content = '\n'.join(fixed_lines)

        # 6. Добавляем пустую строку в конце файла если её нет
        if content and not content.endswith('\n'):
            content += '\n'

        # 7. Исправляем двойные пустые строки между функциями
        content = re.sub(r'\n\n\n+', '\n\n', content)

        # Записываем только если что-то изменилось
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Исправлен: {file_path}")
            return True
        else:
            print(f"- Без изменений: {file_path}")
            return False

    except Exception as e:
        print(f"✗ Ошибка в {file_path}: {e}")
        return False


def main():
    """Основная функция"""
    print("🔧 Автоматическое исправление PEP8...")

    # Исключаем файлы, которые не нужно исправлять
    exclude_dirs = {
        '.git', '__pycache__', 'node_modules', '.venv', 'venv',
        'staticfiles', 'media', 'migrations'
    }

    exclude_files = {
        'fix_pep8_auto.py', 'manage.py', 'wsgi.py', 'asgi.py'
    }

    fixed_count = 0
    total_count = 0

    # Проходим по всем Python файлам
    for root, dirs, files in os.walk('.'):
        # Исключаем директории
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if file.endswith('.py') and file not in exclude_files:
                file_path = os.path.join(root, file)
                total_count += 1

                if fix_pep8_file(file_path):
                    fixed_count += 1

    print("\n📊 Результат:")
    print(f"  Всего файлов: {total_count}")
    print(f"  Исправлено: {fixed_count}")
    print(f"  Без изменений: {total_count - fixed_count}")


if __name__ == '__main__':
    main()
