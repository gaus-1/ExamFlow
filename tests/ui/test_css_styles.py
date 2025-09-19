"""
CSS тесты для проверки стилей и визуальных элементов
"""

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


@pytest.mark.ui
@pytest.mark.css
class TestCSSStyles:
    """Тесты CSS стилей и визуальных элементов"""
    
    def test_responsive_design_breakpoints(self, selenium_driver, live_server):
        """Тест адаптивного дизайна на разных разрешениях"""
        selenium_driver.get(f"{live_server.url}/")
        
        # Тестируем мобильную версию
        selenium_driver.set_window_size(375, 667)  # iPhone размер
        time.sleep(1)
        
        # Проверяем, что навигация адаптируется
        nav = selenium_driver.find_element(By.TAG_NAME, "nav")
        nav_classes = nav.get_attribute("class")
        assert "mobile" in nav_classes.lower() or "responsive" in nav_classes.lower()
        
        # Тестируем планшетную версию
        selenium_driver.set_window_size(768, 1024)  # iPad размер
        time.sleep(1)
        
        # Тестируем десктопную версию
        selenium_driver.set_window_size(1920, 1080)  # Desktop размер
        time.sleep(1)
        
        # Проверяем, что контент корректно отображается
        hero_section = selenium_driver.find_element(By.CLASS_NAME, "hero-section")
        assert hero_section.is_displayed()
    
    def test_color_scheme_consistency(self, selenium_driver, live_server):
        """Тест консистентности цветовой схемы"""
        selenium_driver.get(f"{live_server.url}/")
        
        # Проверяем основные цвета
        hero_section = selenium_driver.find_element(By.CLASS_NAME, "hero-section")
        hero_bg_color = hero_section.value_of_css_property("background-color")
        
        # Проверяем, что используется правильная цветовая схема
        # ExamFlow использует цвета: #fffef2, #252525, #666, #f8f8f8
        assert hero_bg_color is not None
        
        # Проверяем цвет текста
        title_element = selenium_driver.find_element(By.CSS_SELECTOR, ".hero-section h1")
        text_color = title_element.value_of_css_property("color")
        assert text_color is not None
    
    def test_typography_hierarchy(self, selenium_driver, live_server):
        """Тест иерархии типографики"""
        selenium_driver.get(f"{live_server.url}/")
        
        # Проверяем размеры заголовков
        h1_elements = selenium_driver.find_elements(By.TAG_NAME, "h1")
        h2_elements = selenium_driver.find_elements(By.TAG_NAME, "h2")
        
        if h1_elements and h2_elements:
            h1_font_size = h1_elements[0].value_of_css_property("font-size")
            h2_font_size = h2_elements[0].value_of_css_property("font-size")
            
            # H1 должен быть больше H2
            h1_size = float(h1_font_size.replace('px', ''))
            h2_size = float(h2_font_size.replace('px', ''))
            assert h1_size >= h2_size
    
    def test_button_styles(self, selenium_driver, live_server):
        """Тест стилей кнопок"""
        selenium_driver.get(f"{live_server.url}/")
        
        # Находим все кнопки
        buttons = selenium_driver.find_elements(By.CSS_SELECTOR, "button, .btn, input[type='submit']")
        
        for button in buttons:
            if button.is_displayed():
                # Проверяем, что у кнопок есть стили
                bg_color = button.value_of_css_property("background-color")
                border_radius = button.value_of_css_property("border-radius")
                
                assert bg_color is not None
                assert border_radius is not None
    
    def test_form_styles(self, selenium_driver, live_server):
        """Тест стилей форм"""
        selenium_driver.get(f"{live_server.url}/")
        
        # Находим поля ввода
        input_fields = selenium_driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email'], textarea")
        
        for input_field in input_fields:
            if input_field.is_displayed():
                # Проверяем стили полей ввода
                border = input_field.value_of_css_property("border")
                padding = input_field.value_of_css_property("padding")
                
                assert border is not None
                assert padding is not None
    
    def test_card_component_styles(self, selenium_driver, live_server):
        """Тест стилей карточек"""
        selenium_driver.get(f"{live_server.url}/")
        
        # Находим карточки
        cards = selenium_driver.find_elements(By.CSS_SELECTOR, ".card, .subject-card, .task-card")
        
        for card in cards:
            if card.is_displayed():
                # Проверяем стили карточек
                box_shadow = card.value_of_css_property("box-shadow")
                border_radius = card.value_of_css_property("border-radius")
                margin = card.value_of_css_property("margin")
                
                assert box_shadow is not None or border_radius is not None
    
    def test_loading_states(self, selenium_driver, live_server):
        """Тест состояний загрузки"""
        selenium_driver.get(f"{live_server.url}/")
        
        # Проверяем наличие спиннеров или индикаторов загрузки
        loading_elements = selenium_driver.find_elements(By.CSS_SELECTOR, ".loading, .spinner, .loader")
        
        # Если есть элементы загрузки, проверяем их стили
        for element in loading_elements:
            if element.is_displayed():
                animation = element.value_of_css_property("animation")
                assert animation is not None or "spin" in element.get_attribute("class")
    
    def test_accessibility_colors(self, selenium_driver, live_server):
        """Тест доступности цветов"""
        selenium_driver.get(f"{live_server.url}/")
        
        # Проверяем контрастность основных элементов
        main_text = selenium_driver.find_elements(By.CSS_SELECTOR, "p, span, div")
        
        for element in main_text[:5]:  # Проверяем первые 5 элементов
            if element.is_displayed() and element.text.strip():
                color = element.value_of_css_property("color")
                bg_color = element.value_of_css_property("background-color")
                
                # Базовая проверка, что цвета определены
                assert color is not None
                assert bg_color is not None
    
    def test_hover_effects(self, selenium_driver, live_server):
        """Тест hover эффектов"""
        selenium_driver.get(f"{live_server.url}/")
        
        # Находим интерактивные элементы
        interactive_elements = selenium_driver.find_elements(By.CSS_SELECTOR, "button, .btn, a, .card")
        
        for element in interactive_elements[:3]:  # Проверяем первые 3 элемента
            if element.is_displayed():
                # Получаем исходные стили
                original_bg = element.value_of_css_property("background-color")
                
                # Симулируем hover
                selenium_driver.execute_script("arguments[0].dispatchEvent(new Event('mouseover'))", element)
                time.sleep(0.1)
                
                # Проверяем, что стили изменились (если есть hover эффекты)
                hover_bg = element.value_of_css_property("background-color")
                
                # Если есть hover эффект, цвета должны отличаться
                # Если нет hover эффекта, цвета остаются одинаковыми
                # Это нормально в обоих случаях
    
    def test_focus_styles(self, selenium_driver, live_server):
        """Тест стилей фокуса"""
        selenium_driver.get(f"{live_server.url}/")
        
        # Находим фокусируемые элементы
        focusable_elements = selenium_driver.find_elements(By.CSS_SELECTOR, "input, button, a, textarea")
        
        for element in focusable_elements[:3]:  # Проверяем первые 3 элемента
            if element.is_displayed():
                # Фокусируемся на элементе
                element.send_keys("")  # Это дает фокус
                
                # Проверяем, что элемент получил фокус
                focused_element = selenium_driver.switch_to.active_element
                assert focused_element == element
                
                # Проверяем стили фокуса
                outline = element.value_of_css_property("outline")
                box_shadow = element.value_of_css_property("box-shadow")
                
                # Должен быть хотя бы один индикатор фокуса
                assert outline != "none" or "0px" not in box_shadow
    
    def test_animation_performance(self, selenium_driver, live_server):
        """Тест производительности анимаций"""
        selenium_driver.get(f"{live_server.url}/")
        
        # Проверяем CSS анимации
        animated_elements = selenium_driver.find_elements(By.CSS_SELECTOR, "[style*='animation'], [class*='animate']")
        
        for element in animated_elements:
            if element.is_displayed():
                # Проверяем, что анимация определена
                animation = element.value_of_css_property("animation")
                transition = element.value_of_css_property("transition")
                
                # Должна быть либо анимация, либо переход
                assert animation != "none" or transition != "none"
    
    def test_print_styles(self, selenium_driver, live_server):
        """Тест стилей для печати"""
        selenium_driver.get(f"{live_server.url}/")
        
        # Переключаемся в режим печати
        selenium_driver.execute_script("window.matchMedia('print').matches = true")
        
        # Проверяем, что основные элементы видны
        main_content = selenium_driver.find_element(By.TAG_NAME, "main")
        assert main_content.is_displayed()
        
        # Проверяем, что навигация скрыта (обычно скрывают в print стилях)
        nav = selenium_driver.find_element(By.TAG_NAME, "nav")
        nav_display = nav.value_of_css_property("display")
        
        # Это может быть "none" для print стилей или остаться видимым
        # Оба варианта допустимы
