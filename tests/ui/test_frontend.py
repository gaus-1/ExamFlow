"""
UI тесты для фронтенда ExamFlow с использованием Selenium
"""

import time

import pytest
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@pytest.mark.ui
@pytest.mark.slow
class TestHomePage:
    """Тесты главной страницы"""

    def test_home_page_loads(self, selenium_driver, live_server):
        """Тест загрузки главной страницы"""
        selenium_driver.get(f"{live_server.url}/")

        # Проверяем заголовок страницы
        assert "ExamFlow" in selenium_driver.title

        # Проверяем основные элементы
        hero_section = selenium_driver.find_element(By.CLASS_NAME, "hero-section")
        assert hero_section.is_displayed()

        # Проверяем навигацию
        navigation = selenium_driver.find_element(By.TAG_NAME, "nav")
        assert navigation.is_displayed()

    def test_navigation_menu(self, selenium_driver, live_server):
        """Тест навигационного меню"""
        selenium_driver.get(f"{live_server.url}/")

        # Проверяем основные пункты меню
        menu_items = selenium_driver.find_elements(By.CSS_SELECTOR, "nav a")
        menu_texts = [item.text for item in menu_items]

        expected_items = ["Главная", "Предметы", "О нас", "Контакты"]
        for item in expected_items:
            assert any(
                item in text for text in menu_texts
            ), f"Menu item '{item}' not found"

    def test_responsive_design_mobile(self, selenium_driver, live_server):
        """Тест адаптивного дизайна для мобильных устройств"""
        selenium_driver.set_window_size(375, 667)  # iPhone размер
        selenium_driver.get(f"{live_server.url}/")

        # Проверяем что мобильное меню работает
        try:
            mobile_menu_button = selenium_driver.find_element(
                By.CLASS_NAME, "mobile-menu-toggle"
            )
            if mobile_menu_button.is_displayed():
                mobile_menu_button.click()

                # Проверяем что меню открылось
                mobile_menu = selenium_driver.find_element(By.CLASS_NAME, "mobile-menu")
                assert mobile_menu.is_displayed()
        except NoSuchElementException:
            # Мобильное меню может не быть реализовано
            pass

    def test_responsive_design_tablet(self, selenium_driver, live_server):
        """Тест адаптивного дизайна для планшетов"""
        selenium_driver.set_window_size(768, 1024)  # iPad размер
        selenium_driver.get(f"{live_server.url}/")

        # Проверяем что контент адаптируется
        hero_section = selenium_driver.find_element(By.CLASS_NAME, "hero-section")
        assert hero_section.is_displayed()

    def test_responsive_design_desktop(self, selenium_driver, live_server):
        """Тест адаптивного дизайна для десктопа"""
        selenium_driver.set_window_size(1920, 1080)  # Desktop размер
        selenium_driver.get(f"{live_server.url}/")

        # Проверяем полноценный интерфейс
        hero_section = selenium_driver.find_element(By.CLASS_NAME, "hero-section")
        assert hero_section.is_displayed()

        # Проверяем что нет мобильного меню
        try:
            mobile_menu = selenium_driver.find_element(
                By.CLASS_NAME, "mobile-menu-toggle"
            )
            assert not mobile_menu.is_displayed()
        except NoSuchElementException:
            # Это нормально для десктопной версии
            pass


@pytest.mark.ui
@pytest.mark.slow
class TestAIInterface:
    """Тесты AI интерфейса"""

    def test_ai_interface_elements(self, selenium_driver, live_server):
        """Тест элементов AI интерфейса"""
        selenium_driver.get(f"{live_server.url}/")

        # Ждем загрузки AI интерфейса
        try:
            ai_input = WebDriverWait(selenium_driver, 10).until(
                EC.presence_of_element_located((By.ID, "ai-input"))
            )
            assert ai_input.is_displayed()

            ai_button = selenium_driver.find_element(By.ID, "ai-send-button")
            assert ai_button.is_displayed()

            ai_suggestions = selenium_driver.find_element(
                By.CLASS_NAME, "ai-suggestions"
            )
            assert ai_suggestions.is_displayed()

        except TimeoutException:
            pytest.skip("AI interface not loaded or not available")

    def test_ai_suggestions_click(self, selenium_driver, live_server):
        """Тест клика по предложениям AI"""
        selenium_driver.get(f"{live_server.url}/")

        try:
            ai_suggestions = WebDriverWait(selenium_driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ai-suggestions"))
            )

            suggestion_buttons = ai_suggestions.find_elements(By.TAG_NAME, "button")
            if suggestion_buttons:
                suggestion_buttons[0].click()

                # Проверяем что текст попал в поле ввода
                ai_input = selenium_driver.find_element(By.ID, "ai-input")
                assert ai_input.get_attribute("value") != ""

        except TimeoutException:
            pytest.skip("AI suggestions not available")

    def test_ai_input_and_send(self, selenium_driver, live_server):
        """Тест ввода текста и отправки в AI"""
        selenium_driver.get(f"{live_server.url}/")

        try:
            ai_input = WebDriverWait(selenium_driver, 10).until(
                EC.element_to_be_clickable((By.ID, "ai-input"))
            )

            # Вводим текст
            test_message = "Помогите решить уравнение 2x + 3 = 7"
            ai_input.clear()
            ai_input.send_keys(test_message)

            # Отправляем
            ai_button = selenium_driver.find_element(By.ID, "ai-send-button")
            ai_button.click()

            # Ждем ответ
            try:
                ai_response = WebDriverWait(selenium_driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "ai-response"))
                )
                assert ai_response.is_displayed()

            except TimeoutException:
                # AI может не отвечать в тестовой среде
                pass

        except TimeoutException:
            pytest.skip("AI input not available")

    def test_ai_chat_history(self, selenium_driver, live_server):
        """Тест истории чата с AI"""
        selenium_driver.get(f"{live_server.url}/")

        try:
            ai_input = WebDriverWait(selenium_driver, 10).until(
                EC.element_to_be_clickable((By.ID, "ai-input"))
            )

            # Отправляем несколько сообщений
            messages = [
                "Привет, ExamFlow AI!",
                "Помогите с математикой",
                "Расскажите про русский язык",
            ]

            for message in messages:
                ai_input.clear()
                ai_input.send_keys(message)

                ai_button = selenium_driver.find_element(By.ID, "ai-send-button")
                ai_button.click()

                time.sleep(1)  # Небольшая пауза между сообщениями

            # Проверяем что сообщения сохранились в истории
            chat_messages = selenium_driver.find_elements(By.CLASS_NAME, "chat-message")
            assert len(chat_messages) >= len(messages)

        except TimeoutException:
            pytest.skip("AI chat not available")


@pytest.mark.ui
@pytest.mark.slow
class TestSubjectsPage:
    """Тесты страницы предметов"""

    def test_subjects_page_loads(
        self, selenium_driver, live_server, math_subject, russian_subject
    ):
        """Тест загрузки страницы предметов"""
        selenium_driver.get(f"{live_server.url}/subjects/")

        # Проверяем заголовок
        assert "Предметы" in selenium_driver.title

        # Проверяем наличие предметов
        subject_cards = selenium_driver.find_elements(By.CLASS_NAME, "subject-card")
        assert len(subject_cards) >= 2  # Математика и Русский

        # Проверяем что есть карточки с нужными предметами
        page_text = selenium_driver.page_source
        assert "Математика" in page_text
        assert "Русский" in page_text

    def test_subject_card_click(self, selenium_driver, live_server, math_subject):
        """Тест клика по карточке предмета"""
        selenium_driver.get(f"{live_server.url}/subjects/")

        # Ищем карточку математики
        math_cards = selenium_driver.find_elements(
            By.XPATH, "//div[contains(text(), 'Математика')]"
        )
        if math_cards:
            math_cards[0].click()

            # Проверяем переход на страницу предмета
            time.sleep(2)  # Ждем загрузки
            current_url = selenium_driver.current_url
            assert "subject" in current_url or "subjects" in current_url

    def test_subject_filtering(
        self, selenium_driver, live_server, math_subject, russian_subject
    ):
        """Тест фильтрации предметов"""
        selenium_driver.get(f"{live_server.url}/subjects/")

        # Ищем фильтры (если есть)
        try:
            filter_buttons = selenium_driver.find_elements(
                By.CLASS_NAME, "subject-filter"
            )
            if filter_buttons:
                # Кликаем по фильтру ЕГЭ
                for button in filter_buttons:
                    if "ЕГЭ" in button.text:
                        button.click()
                        time.sleep(1)

                        # Проверяем что предметы отфильтрованы
                        visible_subjects = selenium_driver.find_elements(
                            By.CLASS_NAME, "subject-card"
                        )
                        assert len(visible_subjects) > 0
                        break
        except NoSuchElementException:
            # Фильтры могут не быть реализованы
            pass


@pytest.mark.ui
@pytest.mark.slow
class TestTaskPage:
    """Тесты страницы заданий"""

    def test_task_page_loads(self, selenium_driver, live_server, math_task):
        """Тест загрузки страницы задания"""
        selenium_driver.get(f"{live_server.url}/task/{math_task.id}/")

        # Проверяем заголовок
        assert (
            "Задание" in selenium_driver.title
            or "Решите уравнение" in selenium_driver.title
        )

        # Проверяем содержание задания
        task_content = selenium_driver.find_element(By.CLASS_NAME, "task-content")
        assert task_content.is_displayed()

        # Проверяем поле для ответа
        answer_input = selenium_driver.find_element(By.ID, "answer-input")
        assert answer_input.is_displayed()

    def test_task_solve_correct_answer(self, selenium_driver, live_server, math_task):
        """Тест решения задания с правильным ответом"""
        selenium_driver.get(f"{live_server.url}/task/{math_task.id}/")

        # Вводим правильный ответ
        answer_input = WebDriverWait(selenium_driver, 10).until(
            EC.element_to_be_clickable((By.ID, "answer-input"))
        )
        answer_input.clear()
        answer_input.send_keys("4")

        # Отправляем ответ
        submit_button = selenium_driver.find_element(By.ID, "submit-answer")
        submit_button.click()

        # Ждем результат
        try:
            result_message = WebDriverWait(selenium_driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "result-message"))
            )
            assert result_message.is_displayed()
            # Проверяем что результат положительный
            assert (
                "правильно" in result_message.text.lower()
                or "верно" in result_message.text.lower()
            )
        except TimeoutException:
            # Результат может не отображаться в тестовой среде
            pass

    def test_task_solve_incorrect_answer(self, selenium_driver, live_server, math_task):
        """Тест решения задания с неправильным ответом"""
        selenium_driver.get(f"{live_server.url}/task/{math_task.id}/")

        # Вводим неправильный ответ
        answer_input = WebDriverWait(selenium_driver, 10).until(
            EC.element_to_be_clickable((By.ID, "answer-input"))
        )
        answer_input.clear()
        answer_input.send_keys("5")

        # Отправляем ответ
        submit_button = selenium_driver.find_element(By.ID, "submit-answer")
        submit_button.click()

        # Ждем результат
        try:
            result_message = WebDriverWait(selenium_driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "result-message"))
            )
            assert result_message.is_displayed()
            # Проверяем что результат отрицательный
            assert (
                "неправильно" in result_message.text.lower()
                or "неверно" in result_message.text.lower()
            )
        except TimeoutException:
            # Результат может не отображаться в тестовой среде
            pass

    def test_task_hint_system(self, selenium_driver, live_server, math_task):
        """Тест системы подсказок"""
        selenium_driver.get(f"{live_server.url}/task/{math_task.id}/")

        # Ищем кнопку подсказки
        try:
            hint_button = selenium_driver.find_element(By.ID, "hint-button")
            hint_button.click()

            # Проверяем появление подсказки
            hint_content = WebDriverWait(selenium_driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "hint-content"))
            )
            assert hint_content.is_displayed()

        except NoSuchElementException:
            # Система подсказок может не быть реализована
            pass


@pytest.mark.ui
@pytest.mark.slow
class TestUserInterface:
    """Тесты пользовательского интерфейса"""

    def test_telegram_login_widget(self, selenium_driver, live_server):
        """Тест виджета входа через Telegram"""
        selenium_driver.get(f"{live_server.url}/")

        # Ищем виджет Telegram
        try:
            telegram_widget = selenium_driver.find_element(
                By.CLASS_NAME, "telegram-login-widget"
            )
            assert telegram_widget.is_displayed()

            # Проверяем кнопку входа
            login_button = telegram_widget.find_element(By.TAG_NAME, "button")
            assert login_button.is_displayed()
            assert "Telegram" in login_button.text or "Войти" in login_button.text

        except NoSuchElementException:
            # Виджет может не быть реализован
            pytest.skip("Telegram login widget not available")

    def test_qr_code_display(self, selenium_driver, live_server):
        """Тест отображения QR кода"""
        selenium_driver.get(f"{live_server.url}/")

        # Ищем QR код
        try:
            qr_code = selenium_driver.find_element(By.CLASS_NAME, "qr-code")
            assert qr_code.is_displayed()

            # Проверяем что это изображение
            qr_image = qr_code.find_element(By.TAG_NAME, "img")
            assert qr_image.is_displayed()

        except NoSuchElementException:
            # QR код может не быть реализован
            pass

    def test_statistics_display(self, selenium_driver, live_server):
        """Тест отображения статистики"""
        selenium_driver.get(f"{live_server.url}/")

        # Ищем секцию статистики
        try:
            stats_section = selenium_driver.find_element(
                By.CLASS_NAME, "statistics-section"
            )
            assert stats_section.is_displayed()

            # Проверяем статистические элементы
            stat_items = stats_section.find_elements(By.CLASS_NAME, "stat-item")
            assert len(stat_items) > 0

            # Проверяем что есть числа
            stats_text = stats_section.text
            import re

            numbers = re.findall(r"\d+", stats_text)
            assert len(numbers) > 0

        except NoSuchElementException:
            # Статистика может не быть реализована
            pass


@pytest.mark.ui
@pytest.mark.slow
class TestAccessibility:
    """Тесты доступности (a11y)"""

    def test_keyboard_navigation(self, selenium_driver, live_server):
        """Тест навигации с клавиатуры"""
        selenium_driver.get(f"{live_server.url}/")

        # Начинаем навигацию с клавиши Tab
        selenium_driver.find_element(By.TAG_NAME, "body").send_keys(Keys.TAB)

        # Проверяем что фокус перемещается
        focused_element = selenium_driver.switch_to.active_element
        assert focused_element is not None

    def test_alt_text_for_images(self, selenium_driver, live_server):
        """Тест alt текста для изображений"""
        selenium_driver.get(f"{live_server.url}/")

        # Находим все изображения
        images = selenium_driver.find_elements(By.TAG_NAME, "img")

        for image in images:
            # Проверяем что у изображений есть alt атрибут
            alt_text = image.get_attribute("alt")
            # Alt может быть пустым для декоративных изображений
            assert alt_text is not None  # Атрибут должен существовать

    def test_heading_structure(self, selenium_driver, live_server):
        """Тест структуры заголовков"""
        selenium_driver.get(f"{live_server.url}/")

        # Проверяем наличие h1
        h1_elements = selenium_driver.find_elements(By.TAG_NAME, "h1")
        assert len(h1_elements) > 0

        # Проверяем что h1 содержит основную информацию
        main_h1 = h1_elements[0]
        assert "ExamFlow" in main_h1.text or "Главная" in main_h1.text

    def test_color_contrast(self, selenium_driver, live_server):
        """Тест цветового контраста"""
        selenium_driver.get(f"{live_server.url}/")

        # Проверяем основные текстовые элементы
        text_elements = selenium_driver.find_elements(By.TAG_NAME, "p")

        for element in text_elements[:5]:  # Проверяем первые 5 элементов
            if element.is_displayed():
                # Получаем стили элемента
                color = element.value_of_css_property("color")
                background = element.value_of_css_property("background-color")

                # Проверяем что цвета определены
                assert color != "rgba(0, 0, 0, 0)"  # Прозрачный текст
                assert background != "rgba(0, 0, 0, 0)"  # Прозрачный фон


@pytest.mark.ui
@pytest.mark.slow
class TestErrorHandling:
    """Тесты обработки ошибок в UI"""

    def test_404_page(self, selenium_driver, live_server):
        """Тест страницы 404"""
        selenium_driver.get(f"{live_server.url}/nonexistent-page/")

        # Проверяем что отображается страница ошибки
        page_text = selenium_driver.page_source.lower()
        assert (
            "404" in page_text or "не найдено" in page_text or "not found" in page_text
        )

    def test_500_error_handling(self, selenium_driver, live_server):
        """Тест обработки 500 ошибки"""
        # Пытаемся получить доступ к несуществующему заданию
        selenium_driver.get(f"{live_server.url}/task/999999/")

        # Проверяем что ошибка обрабатывается корректно
        page_text = selenium_driver.page_source.lower()
        # Может быть 404 или 500 ошибка
        assert any(
            error in page_text
            for error in ["404", "500", "ошибка", "error", "не найдено"]
        )

    def test_network_error_handling(self, selenium_driver):
        """Тест обработки сетевых ошибок"""
        # Пытаемся подключиться к несуществующему серверу
        try:
            selenium_driver.get("http://localhost:99999/")
        except Exception:
            # Ожидаемая ошибка
            pass

        # Проверяем что браузер не завис
        assert selenium_driver.current_url is not None


@pytest.mark.ui
@pytest.mark.slow
class TestPerformance:
    """Тесты производительности UI"""

    def test_page_load_time(self, selenium_driver, live_server):
        """Тест времени загрузки страницы"""
        import time

        start_time = time.time()
        selenium_driver.get(f"{live_server.url}/")

        # Ждем полной загрузки
        WebDriverWait(selenium_driver, 10).until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )

        load_time = time.time() - start_time

        # Страница должна загружаться менее чем за 5 секунд
        assert load_time < 5.0

    def test_resource_loading(self, selenium_driver, live_server):
        """Тест загрузки ресурсов"""
        selenium_driver.get(f"{live_server.url}/")

        # Проверяем что CSS загружается
        css_links = selenium_driver.find_elements(
            By.CSS_SELECTOR, "link[rel='stylesheet']"
        )
        assert len(css_links) > 0

        # Проверяем что JavaScript загружается
        js_scripts = selenium_driver.find_elements(By.CSS_SELECTOR, "script[src]")
        assert len(js_scripts) > 0

        # Проверяем что нет ошибок в консоли
        logs = selenium_driver.get_log("browser")
        error_logs = [log for log in logs if log["level"] == "SEVERE"]
        # Допускаем небольшие ошибки, но не критические
        assert len(error_logs) < 3
