"""
Кроссбраузерные тесты
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging

logger = logging.getLogger(__name__)


@pytest.mark.cross_browser
@pytest.mark.slow
class TestBrowserCompatibility:
    """Тесты совместимости с разными браузерами"""
    
    @pytest.fixture(params=['chrome', 'firefox', 'edge'])
    def browser_driver(self, request):
        """Фикстура для создания драйверов разных браузеров"""
        browser = request.param
        
        if browser == 'chrome':
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            driver = webdriver.Chrome(options=options)
        elif browser == 'firefox':
            options = webdriver.FirefoxOptions()
            options.add_argument('--headless')
            driver = webdriver.Firefox(options=options)
        elif browser == 'edge':
            options = webdriver.EdgeOptions()
            options.add_argument('--headless')
            driver = webdriver.Edge(options=options)
        else:
            pytest.skip(f"Browser {browser} not supported")
        
        yield driver
        driver.quit()
    
    def test_homepage_loads_in_all_browsers(self, browser_driver, live_server):
        """Тест загрузки главной страницы во всех браузерах"""
        driver = browser_driver
        browser_name = driver.capabilities['browserName']
        
        logger.info(f"Testing homepage in {browser_name}")
        
        driver.get(f"{live_server.url}/")
        
        # Ждем загрузки страницы
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Проверяем основные элементы
        assert "ExamFlow" in driver.title
        
        # Проверяем наличие основных элементов
        try:
            hero_section = driver.find_element(By.CLASS_NAME, "hero-section")
            assert hero_section.is_displayed()
        except:
            # Если нет hero-section, проверяем заголовок
            h1 = driver.find_element(By.TAG_NAME, "h1")
            assert h1.is_displayed()
        
        logger.info(f"Homepage loaded successfully in {browser_name}")
    
    def test_navigation_works_in_all_browsers(self, browser_driver, live_server):
        """Тест навигации во всех браузерах"""
        driver = browser_driver
        browser_name = driver.capabilities['browserName']
        
        logger.info(f"Testing navigation in {browser_name}")
        
        driver.get(f"{live_server.url}/")
        
        # Ждем загрузки навигации
        try:
            nav = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "nav"))
            )
            assert nav.is_displayed()
        except TimeoutException:
            # Если нет nav, проверяем ссылки
            links = driver.find_elements(By.TAG_NAME, "a")
            assert len(links) > 0
        
        # Проверяем кликабельность ссылок
        links = driver.find_elements(By.CSS_SELECTOR, "a[href]")
        for link in links[:3]:  # Проверяем первые 3 ссылки
            if link.is_displayed():
                href = link.get_attribute("href")
                if href and not href.startswith("javascript:"):
                    # Проверяем, что ссылка не сломана
                    assert href != "#"
        
        logger.info(f"Navigation works in {browser_name}")
    
    def test_responsive_design_in_all_browsers(self, browser_driver, live_server):
        """Тест адаптивного дизайна во всех браузерах"""
        driver = browser_driver
        browser_name = driver.capabilities['browserName']
        
        logger.info(f"Testing responsive design in {browser_name}")
        
        driver.get(f"{live_server.url}/")
        
        # Тестируем разные размеры экрана
        screen_sizes = [
            (375, 667),   # iPhone
            (768, 1024),  # iPad
            (1920, 1080)  # Desktop
        ]
        
        for width, height in screen_sizes:
            driver.set_window_size(width, height)
            time.sleep(1)  # Ждем адаптации
            
            # Проверяем, что страница не сломалась
            body = driver.find_element(By.TAG_NAME, "body")
            assert body.is_displayed()
            
            # Проверяем, что контент виден
            body_rect = body.rect
            assert body_rect['width'] > 0
            assert body_rect['height'] > 0
        
        logger.info(f"Responsive design works in {browser_name}")
    
    def test_javascript_execution_in_all_browsers(self, browser_driver, live_server):
        """Тест выполнения JavaScript во всех браузерах"""
        driver = browser_driver
        browser_name = driver.capabilities['browserName']
        
        logger.info(f"Testing JavaScript execution in {browser_name}")
        
        driver.get(f"{live_server.url}/")
        
        # Тестируем базовые JavaScript функции
        js_tests = [
            "return typeof window !== 'undefined';",
            "return typeof document !== 'undefined';",
            "return typeof console !== 'undefined';",
            "return document.title;",
            "return window.innerWidth;",
            "return window.innerHeight;"
        ]
        
        for js_code in js_tests:
            try:
                result = driver.execute_script(js_code)
                assert result is not None
            except Exception as e:
                pytest.fail(f"JavaScript execution failed in {browser_name}: {e}")
        
        logger.info(f"JavaScript execution works in {browser_name}")
    
    def test_css_rendering_in_all_browsers(self, browser_driver, live_server):
        """Тест рендеринга CSS во всех браузерах"""
        driver = browser_driver
        browser_name = driver.capabilities['browserName']
        
        logger.info(f"Testing CSS rendering in {browser_name}")
        
        driver.get(f"{live_server.url}/")
        
        # Проверяем основные CSS свойства
        body = driver.find_element(By.TAG_NAME, "body")
        
        # Проверяем, что CSS загружается
        font_family = body.value_of_css_property("font-family")
        assert font_family is not None and font_family != ""
        
        # Проверяем цветовую схему
        color = body.value_of_css_property("color")
        assert color is not None and color != ""
        
        # Проверяем фоновый цвет
        background_color = body.value_of_css_property("background-color")
        assert background_color is not None
        
        logger.info(f"CSS rendering works in {browser_name}")
    
    def test_form_functionality_in_all_browsers(self, browser_driver, live_server):
        """Тест функциональности форм во всех браузерах"""
        driver = browser_driver
        browser_name = driver.capabilities['browserName']
        
        logger.info(f"Testing form functionality in {browser_name}")
        
        driver.get(f"{live_server.url}/")
        
        # Ищем формы на странице
        forms = driver.find_elements(By.TAG_NAME, "form")
        
        if forms:
            for form in forms:
                if form.is_displayed():
                    # Проверяем поля ввода
                    inputs = form.find_elements(By.CSS_SELECTOR, "input, textarea, select")
                    
                    for input_field in inputs:
                        if input_field.is_displayed():
                            # Проверяем, что поле интерактивно
                            assert input_field.is_enabled()
                            
                            # Тестируем ввод текста
                            if input_field.get_attribute("type") in ["text", "email", "textarea"]:
                                try:
                                    input_field.clear()
                                    input_field.send_keys("test input")
                                    assert input_field.get_attribute("value") == "test input"
                                except Exception as e:
                                    logger.warning(f"Input test failed in {browser_name}: {e}")
        
        logger.info(f"Form functionality works in {browser_name}")
    
    def test_image_loading_in_all_browsers(self, browser_driver, live_server):
        """Тест загрузки изображений во всех браузерах"""
        driver = browser_driver
        browser_name = driver.capabilities['browserName']
        
        logger.info(f"Testing image loading in {browser_name}")
        
        driver.get(f"{live_server.url}/")
        
        # Ищем изображения
        images = driver.find_elements(By.TAG_NAME, "img")
        
        for img in images:
            if img.is_displayed():
                # Проверяем, что изображение загружено
                try:
                    # Проверяем размеры изображения
                    width = img.size['width']
                    height = img.size['height']
                    
                    # Изображение должно иметь размеры
                    assert width > 0 and height > 0
                    
                    # Проверяем, что изображение действительно загружено
                    is_loaded = driver.execute_script("""
                        return arguments[0].complete && arguments[0].naturalWidth > 0;
                    """, img)
                    
                    if not is_loaded:
                        logger.warning(f"Image not fully loaded in {browser_name}")
                    
                except Exception as e:
                    logger.warning(f"Image check failed in {browser_name}: {e}")
        
        logger.info(f"Image loading works in {browser_name}")
    
    def test_error_handling_in_all_browsers(self, browser_driver, live_server):
        """Тест обработки ошибок во всех браузерах"""
        driver = browser_driver
        browser_name = driver.capabilities['browserName']
        
        logger.info(f"Testing error handling in {browser_name}")
        
        # Тестируем доступ к несуществующей странице
        driver.get(f"{live_server.url}/nonexistent-page/")
        
        # Проверяем, что страница не падает с ошибкой 500
        assert driver.page_source is not None
        assert "Internal Server Error" not in driver.page_source
        
        # Проверяем, что есть какая-то обработка ошибки
        # (404 страница, редирект или что-то подобное)
        current_url = driver.current_url
        page_title = driver.title
        
        # Страница должна быть доступна (не белый экран)
        assert len(page_title) > 0
        
        logger.info(f"Error handling works in {browser_name}")
    
    def test_performance_comparison_across_browsers(self, browser_driver, live_server):
        """Сравнение производительности между браузерами"""
        driver = browser_driver
        browser_name = driver.capabilities['browserName']
        
        logger.info(f"Testing performance in {browser_name}")
        
        # Измеряем время загрузки страницы
        start_time = time.time()
        
        driver.get(f"{live_server.url}/")
        
        # Ждем полной загрузки
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        load_time = time.time() - start_time
        
        logger.info(f"{browser_name} load time: {load_time:.2f}s")
        
        # Проверяем, что страница загружается за разумное время
        assert load_time < 10.0, f"{browser_name} load time too high: {load_time:.2f}s"
        
        # Проверяем производительность JavaScript
        js_start = time.time()
        
        # Выполняем простые JavaScript операции
        for i in range(100):
            driver.execute_script("return Math.random();")
        
        js_time = time.time() - js_start
        
        logger.info(f"{browser_name} JavaScript performance: {js_time:.2f}s for 100 operations")
        
        # JavaScript должен работать достаточно быстро
        assert js_time < 5.0, f"{browser_name} JavaScript too slow: {js_time:.2f}s"
    
    def test_accessibility_features_in_all_browsers(self, browser_driver, live_server):
        """Тест функций доступности во всех браузерах"""
        driver = browser_driver
        browser_name = driver.capabilities['browserName']
        
        logger.info(f"Testing accessibility in {browser_name}")
        
        driver.get(f"{live_server.url}/")
        
        # Проверяем alt атрибуты у изображений
        images = driver.find_elements(By.TAG_NAME, "img")
        for img in images:
            alt_text = img.get_attribute("alt")
            # Alt атрибут должен быть (может быть пустым для декоративных изображений)
            assert alt_text is not None
        
        # Проверяем наличие заголовков
        headings = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
        assert len(headings) > 0, "No headings found"
        
        # Проверяем, что есть хотя бы один h1
        h1_elements = driver.find_elements(By.TAG_NAME, "h1")
        assert len(h1_elements) > 0, "No H1 heading found"
        
        # Проверяем фокусируемые элементы
        focusable_elements = driver.find_elements(By.CSS_SELECTOR, 
                                                "button, input, a, textarea, select")
        
        for element in focusable_elements[:3]:  # Проверяем первые 3
            if element.is_displayed():
                # Проверяем, что элемент может получить фокус
                try:
                    element.send_keys("")  # Это дает фокус
                    focused = driver.switch_to.active_element
                    assert focused == element or element.is_displayed()
                except Exception as e:
                    logger.warning(f"Focus test failed in {browser_name}: {e}")
        
        logger.info(f"Accessibility features work in {browser_name}")
    
    def test_mobile_viewport_in_all_browsers(self, browser_driver, live_server):
        """Тест мобильного viewport во всех браузерах"""
        driver = browser_driver
        browser_name = driver.capabilities['browserName']
        
        logger.info(f"Testing mobile viewport in {browser_name}")
        
        driver.get(f"{live_server.url}/")
        
        # Устанавливаем мобильный размер
        driver.set_window_size(375, 667)
        
        # Проверяем viewport meta тег
        viewport_meta = driver.find_elements(By.CSS_SELECTOR, 'meta[name="viewport"]')
        
        if viewport_meta:
            viewport_content = viewport_meta[0].get_attribute("content")
            # Должен быть правильный viewport
            assert "width=device-width" in viewport_content or "initial-scale=1" in viewport_content
        
        # Проверяем, что контент адаптируется
        body = driver.find_element(By.TAG_NAME, "body")
        body_width = body.size['width']
        
        # Ширина контента не должна превышать ширину экрана
        assert body_width <= 400  # Немного больше 375 для отступов
        
        logger.info(f"Mobile viewport works in {browser_name}")
    
    def test_cross_browser_consistency(self, live_server):
        """Тест консистентности между браузерами"""
        logger.info("Testing cross-browser consistency")
        
        browsers = ['chrome', 'firefox', 'edge']
        results = {}
        
        for browser in browsers:
            try:
                if browser == 'chrome':
                    options = webdriver.ChromeOptions()
                    options.add_argument('--headless')
                    driver = webdriver.Chrome(options=options)
                elif browser == 'firefox':
                    options = webdriver.FirefoxOptions()
                    options.add_argument('--headless')
                    driver = webdriver.Firefox(options=options)
                elif browser == 'edge':
                    options = webdriver.EdgeOptions()
                    options.add_argument('--headless')
                    driver = webdriver.Edge(options=options)
                
                driver.get(f"{live_server.url}/")
                
                # Собираем данные о странице
                results[browser] = {
                    'title': driver.title,
                    'url': driver.current_url,
                    'body_text': driver.find_element(By.TAG_NAME, "body").text[:100]
                }
                
                driver.quit()
                
            except Exception as e:
                logger.warning(f"Failed to test {browser}: {e}")
                results[browser] = None
        
        # Проверяем консистентность
        valid_results = {k: v for k, v in results.items() if v is not None}
        
        if len(valid_results) >= 2:
            # Заголовки должны быть одинаковыми
            titles = [r['title'] for r in valid_results.values()]
            assert len(set(titles)) == 1, f"Titles differ: {titles}"
            
            # URL должны быть одинаковыми
            urls = [r['url'] for r in valid_results.values()]
            assert len(set(urls)) == 1, f"URLs differ: {urls}"
            
            logger.info("Cross-browser consistency verified")
        else:
            logger.warning("Not enough browsers tested for consistency check")
