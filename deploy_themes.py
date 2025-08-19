#!/usr/bin/env python3
"""
Скрипт для деплоя переключателя дизайнов на ExamFlow
"""

import os
import shutil
from pathlib import Path

def deploy_themes():
    """Деплой переключателя дизайнов"""
    print("🎨 ДЕПЛОЙ ПЕРЕКЛЮЧАТЕЛЯ ДИЗАЙНОВ EXAMFLOW")
    print("=" * 50)
    
    # Проверяем, что мы в правильной директории
    if not os.path.exists('templates/base.html'):
        print("❌ Ошибка: templates/base.html не найден")
        print("   Запустите скрипт из корневой директории проекта")
        return False
    
    # Проверяем, что модуль themes существует
    if not os.path.exists('themes/'):
        print("❌ Ошибка: модуль themes не найден")
        return False
    
    print("✅ Все необходимые файлы найдены")
    
    # 1. Проверяем, что переключатель уже добавлен в base.html
    with open('templates/base.html', 'r', encoding='utf-8') as f:
        base_content = f.read()
    
    if 'theme-switcher-container' in base_content:
        print("✅ Переключатель дизайнов уже добавлен в base.html")
    else:
        print("❌ Переключатель дизайнов НЕ найден в base.html")
        print("   Нужно добавить HTML код переключателя")
        return False
    
    # 2. Проверяем подключение CSS
    if 'themes.css' in base_content:
        print("✅ CSS файл themes.css подключен")
    else:
        print("❌ CSS файл themes.css НЕ подключен")
        return False
    
    # 3. Проверяем подключение JS
    if 'theme-switcher.js' in base_content:
        print("✅ JS файл theme-switcher.js подключен")
    else:
        print("❌ JS файл theme-switcher.js НЕ подключен")
        return False
    
    # 4. Проверяем, что статические файлы существуют
    css_file = 'themes/static/css/themes.css'
    js_file = 'themes/static/js/theme-switcher.js'
    
    if os.path.exists(css_file):
        print("✅ CSS файл themes.css существует")
    else:
        print("❌ CSS файл themes.css НЕ найден")
        return False
    
    if os.path.exists(js_file):
        print("✅ JS файл theme-switcher.js существует")
    else:
        print("❌ JS файл theme-switcher.js НЕ найден")
        return False
    
    # 5. Собираем статические файлы
    print("\n📦 Сборка статических файлов...")
    try:
        os.system('python manage.py collectstatic --noinput')
        print("✅ Статические файлы собраны")
    except Exception as e:
        print(f"⚠️ Предупреждение при сборе статических файлов: {e}")
    
    # 6. Проверяем финальное состояние
    print("\n🔍 ФИНАЛЬНАЯ ПРОВЕРКА:")
    print("-" * 30)
    
    # Проверяем, что переключатель виден в HTML
    if '🎓 Школьник' in base_content and '👔 Взрослый' in base_content:
        print("✅ Кнопки переключателя найдены в HTML")
    else:
        print("❌ Кнопки переключателя НЕ найдены в HTML")
        return False
    
    # Проверяем атрибут data-theme
    if 'data-theme="school"' in base_content:
        print("✅ Атрибут data-theme добавлен к body")
    else:
        print("❌ Атрибут data-theme НЕ найден")
        return False
    
    print("\n🎉 ПЕРЕКЛЮЧАТЕЛЬ ДИЗАЙНОВ ГОТОВ К ДЕПЛОЮ!")
    print("\n📋 Что нужно сделать дальше:")
    print("1. Закоммитить изменения: git add . && git commit -m 'Add theme switcher'")
    print("2. Запушить на GitHub: git push origin main")
    print("3. Дождаться автоматического деплоя на Render")
    print("4. Проверить работу на https://examflow.ru/")
    
    return True

def check_deployment_status():
    """Проверка статуса деплоя"""
    print("\n🔍 ПРОВЕРКА СТАТУСА ДЕПЛОЯ:")
    print("=" * 30)
    
    # Проверяем git статус
    print("📊 Git статус:")
    os.system('git status --porcelain')
    
    # Проверяем последние коммиты
    print("\n📝 Последние коммиты:")
    os.system('git log --oneline -5')
    
    # Проверяем удаленные ветки
    print("\n🌐 Удаленные ветки:")
    os.system('git remote -v')

if __name__ == "__main__":
    print("🚀 Запуск деплоя переключателя дизайнов...")
    
    if deploy_themes():
        check_deployment_status()
        print("\n✅ Деплой готов! Теперь закоммитьте и запушьте изменения.")
    else:
        print("\n❌ Деплой не удался. Исправьте ошибки и попробуйте снова.")
