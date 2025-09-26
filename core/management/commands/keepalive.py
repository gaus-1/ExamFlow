"""
Команда для поддержания активности всех компонентов ExamFlow 2.0
"""

import logging
import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

# Убираем импорт application - он не нужен для keepalive
# from telegram_bot.bot_main import application
# import asyncio
# import threading

logger = logging.getLogger(__name__)


class KeepaliveService:
    """Сервис для поддержания активности всех компонентов"""

    def __init__(self):
        self.website_url = getattr(
            settings, "WEBSITE_URL", "https://examflow.onrender.com"
        )
        self.health_url = "{self.website_url}/health/"
        self.bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        self.telegram_api_url = "https://api.telegram.org/bot{self.bot_token}/getMe"

    def check_website(self):
        """Проверяет доступность сайта"""
        try:
            response = requests.get(self.health_url, timeout=10)
            if response.status_code == 200:
                logger.info("✅ Сайт активен")
                return True
            else:
                logger.warning("⚠️ Сайт отвечает с кодом {response.status_code}")
                return False
        except Exception:
            logger.error("❌ Ошибка проверки сайта: {e}")
            return False

    def check_database(self):
        """Проверяет подключение к базе данных"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result and result[0] == 1:
                    logger.info("✅ База данных активна")
                    return True
                else:
                    logger.warning("⚠️ База данных не отвечает корректно")
                    return False
        except Exception:
            logger.error("❌ Ошибка проверки базы данных: {e}")
            return False

    def check_bot(self):
        """Проверяет доступность Telegram бота"""
        try:
            response = requests.get(self.telegram_api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    logger.info("✅ Telegram бот активен")
                    return True
                else:
                    logger.warning(
                        "⚠️ Telegram бот не отвечает: {data.get('description')}"
                    )
                    return False
            else:
                logger.warning("⚠️ Telegram API отвечает с кодом {response.status_code}")
                return False
        except Exception:
            logger.error("❌ Ошибка проверки Telegram бота: {e}")
            return False

    def wake_up_website(self):
        """Будит сайт, делая запрос к главной странице"""
        try:
            response = requests.get(self.website_url, timeout=30)
            if response.status_code == 200:
                logger.info("✅ Сайт разбужен успешно")
                return True
            else:
                logger.warning("⚠️ Сайт отвечает с кодом {response.status_code}")
                return False
        except Exception:
            logger.error("❌ Ошибка пробуждения сайта: {e}")
            return False

    def wake_up_database(self):
        """Будит базу данных, выполняя простой запрос"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM core_unifiedprofile")
                result = cursor.fetchone()
                logger.info(
                    "✅ База данных разбужена, профилей: {result[0] if result else 0}"
                )
                return True
        except Exception:
            logger.error("❌ Ошибка пробуждения базы данных: {e}")
            return False

    def run_keepalive_cycle(self, interval=300):  # 5 минут
        """Запускает цикл keepalive"""
        logger.info("🚀 Запуск keepalive цикла с интервалом {interval} секунд")

        while True:
            try:
                logger.info("🔄 Начинаем проверку компонентов...")

                # Проверяем компоненты
                website_ok = self.check_website()
                database_ok = self.check_database()
                bot_ok = self.check_bot()

                # Если что-то не работает, пробуем разбудить
                if not website_ok:
                    logger.info("🌐 Пробуем разбудить сайт...")
                    self.wake_up_website()

                if not database_ok:
                    logger.info("🗄️ Пробуем разбудить базу данных...")
                    self.wake_up_database()

                # Логируем статус
                status = "✅" if all([website_ok, database_ok, bot_ok]) else "⚠️"
                logger.info(
                    "{status} Статус компонентов: Сайт={website_ok}, БД={database_ok}, Бот={bot_ok}"
                )

                # Ждем до следующей проверки
                time.sleep(interval)

            except KeyboardInterrupt:
                logger.info("🛑 Keepalive цикл остановлен пользователем")
                break
            except Exception:
                logger.error("❌ Ошибка в keepalive цикле: {e}")
                time.sleep(60)  # Ждем минуту перед повторной попыткой


class Command(BaseCommand):
    help = "Поддерживает активность всех компонентов ExamFlow 2.0"

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=300,
            help="Интервал проверки в секундах (по умолчанию 300)",
        )
        parser.add_argument(
            "--once",
            action="store_true",
            help="Выполнить проверку один раз и завершить",
        )
        parser.add_argument(
            "--component",
            choices=["website", "database", "bot", "all"],
            default="all",
            help="Проверить только указанный компонент",
        )

    def handle(self, *args, **options):
        keepalive = KeepaliveService()

        if options["once"]:
            # Однократная проверка
            self.stdout.write("🔍 Выполняем однократную проверку компонентов...")

            if options["component"] == "website" or options["component"] == "all":
                website_ok = keepalive.check_website()
                self.stdout.write("Сайт: {'✅' if website_ok else '❌'}")

            if options["component"] == "database" or options["component"] == "all":
                database_ok = keepalive.check_database()
                self.stdout.write("База данных: {'✅' if database_ok else '❌'}")

            if options["component"] == "bot" or options["component"] == "all":
                bot_ok = keepalive.check_bot()
                self.stdout.write("Telegram бот: {'✅' if bot_ok else '❌'}")

            self.stdout.write(self.style.SUCCESS("Проверка завершена"))  # type: ignore

        else:
            # Непрерывный цикл
            self.stdout.write(
                "🚀 Запуск keepalive сервиса с интервалом {options['interval']} секунд"
            )
            self.stdout.write("Нажмите Ctrl+C для остановки")

            try:
                keepalive.run_keepalive_cycle(options["interval"])
            except KeyboardInterrupt:
                self.stdout.write(
                    self.style.WARNING("Keepalive сервис остановлен")
                )  # type: ignore
