#!/usr/bin/env python3
"""
Скрипт для минификации статических ресурсов ExamFlow
"""

import re
from pathlib import Path


def minify_css(css_content: str) -> str:
    """Минификация CSS"""
    # Удаляем комментарии
    css_content = re.sub(r'/\*[\s\S]*?\*/', '', css_content)
    
    # Удаляем лишние пробелы
    css_content = re.sub(r'\s+', ' ', css_content)
    
    # Удаляем пробелы вокруг символов
    css_content = re.sub(r'\s*{\s*', '{', css_content)
    css_content = re.sub(r';\s*', ';', css_content)
    css_content = re.sub(r'}\s*', '}', css_content)
    css_content = re.sub(r':\s*', ':', css_content)
    css_content = re.sub(r',\s*', ',', css_content)
    
    return css_content.strip()


def minify_js(js_content: str) -> str:
    """Минификация JavaScript"""
    # Удаляем однострочные комментарии
    js_content = re.sub(r'//.*$', '', js_content, flags=re.MULTILINE)
    
    # Удаляем многострочные комментарии
    js_content = re.sub(r'/\*[\s\S]*?\*/', '', js_content)
    
    # Удаляем лишние пробелы
    js_content = re.sub(r'\s+', ' ', js_content)
    
    # Удаляем пробелы вокруг операторов
    js_content = re.sub(r'\s*{\s*', '{', js_content)
    js_content = re.sub(r';\s*', ';', js_content)
    js_content = re.sub(r'}\s*', '}', js_content)
    
    return js_content.strip()


def main():
    """Основная функция минификации"""
    base_dir = Path(__file__).parent.parent
    static_dir = base_dir / 'static'
    
    print("🚀 Начинаем минификацию статических ресурсов...")
    
    # Минификация CSS
    css_files = [
        'css/examflow-2.0.css',
    ]
    
    for css_file in css_files:
        css_path = static_dir / css_file
        min_css_path = static_dir / css_file.replace('.css', '.min.css')
        
        if css_path.exists():
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            minified = minify_css(css_content)
            
            with open(min_css_path, 'w', encoding='utf-8') as f:
                f.write(minified)
            
            original_size = len(css_content)
            minified_size = len(minified)
            compression = (1 - minified_size / original_size) * 100
            
            print(f"✅ CSS: {css_file} → {min_css_path.name} ({compression:.1f}% сжатие)")
    
    # Минификация JS
    js_files = [
        'js/core-functions.js',
        'js/examflow-animations.js',
        'js/gamification.js',
    ]
    
    for js_file in js_files:
        js_path = static_dir / js_file
        min_js_path = static_dir / js_file.replace('.js', '.min.js')
        
        if js_path.exists():
            with open(js_path, 'r', encoding='utf-8') as f:
                js_content = f.read()
            
            minified = minify_js(js_content)
            
            with open(min_js_path, 'w', encoding='utf-8') as f:
                f.write(minified)
            
            original_size = len(js_content)
            minified_size = len(minified)
            compression = (1 - minified_size / original_size) * 100
            
            print(f"✅ JS: {js_file} → {min_js_path.name} ({compression:.1f}% сжатие)")
    
    print("🎉 Минификация завершена!")


if __name__ == '__main__':
    main()
