#!/usr/bin/env python3
"""
🎨 Скрипт для генерации PNG иконок
Создает иконки разных размеров для PWA используя только PIL
"""

import os
from PIL import Image, ImageDraw

def create_simple_icon(size):
    """Создает простую иконку заданного размера"""
    # Создаем изображение с фоном
    img = Image.new('RGBA', (size, size), (255, 254, 242, 255))  # #fffef2
    draw = ImageDraw.Draw(img)
    
    # Рисуем основной прямоугольник (книгу)
    margin = size // 8
    book_width = size - 2 * margin
    book_height = int(book_width * 0.6) # Corrected: book_height should be proportional to book_width
    book_x = margin
    book_y = margin
    
    # Фон книги
    draw.rectangle([book_x, book_y, book_x + book_width, book_y + book_height], 
                  fill=(37, 37, 37, 255))  # #252525
    
    # Линии текста
    line_height = book_height // 8
    line_y = book_y + line_height
    for i in range(5):
        line_width = int(book_width * (0.7 - i * 0.05))
        line_x = book_x + (book_width - line_width) // 2
        draw.rectangle([line_x, line_y, line_x + line_width, line_y + 2], 
                      fill=(255, 254, 242, 255))
        line_y += line_height
    
    # Иконка мозга/ИИ внизу
    brain_y = book_y + book_height + margin // 2
    brain_radius = size // 12
    brain_x = size // 2
    
    # Фон мозга
    draw.ellipse([brain_x - brain_radius, brain_y - brain_radius, 
                  brain_x + brain_radius, brain_y + brain_radius], 
                 fill=(248, 248, 248, 255), outline=(37, 37, 37, 255), width=2)
    
    # Глаза
    eye_radius = brain_radius // 4
    draw.ellipse([brain_x - brain_radius//2 - eye_radius, brain_y - eye_radius,
                  brain_x - brain_radius//2 + eye_radius, brain_y + eye_radius], 
                 fill=(37, 37, 37, 255))
    draw.ellipse([brain_x + brain_radius//2 - eye_radius, brain_y - eye_radius,
                  brain_x + brain_radius//2 + eye_radius, brain_y + eye_radius], 
                 fill=(37, 37, 37, 255))
    
    # Акцентный элемент
    accent_radius = size // 18
    accent_x = size - margin - accent_radius
    accent_y = margin + accent_radius
    draw.ellipse([accent_x - accent_radius, accent_y - accent_radius,
                  accent_x + accent_radius, accent_y + accent_radius], 
                 fill=(255, 107, 107, 255))  # #ff6b6b
    
    return img

def main():
    """Основная функция"""
    print("🎨 Генерация иконок для ExamFlow...")
    
    # Размеры иконок
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    # Создаем папку для иконок
    icons_dir = "static/icons"
    os.makedirs(icons_dir, exist_ok=True)
    
    for size in sizes:
        print(f"📱 Создание иконки {size}x{size}...")
        
        # Создаем иконку
        icon = create_simple_icon(size)
        
        # Сохраняем PNG
        filename = f"{icons_dir}/icon-{size}x{size}.png"
        icon.save(filename, "PNG")
        
        print(f"✅ Сохранено: {filename}")
    
    print("🎉 Все иконки созданы успешно!")
    
    # Создаем favicon.ico
    print("🔗 Создание favicon.ico...")
    favicon = create_simple_icon(32)
    favicon.save("static/favicon.ico", "ICO")
    print("✅ Favicon создан: static/favicon.ico")

if __name__ == '__main__':
    main()
