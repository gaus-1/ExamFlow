"""
Система автоматического обновления материалов ФИПИ
"""

import schedule
import time
import threading
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.management import call_command
from django.conf import settings
from core.fipi_loader import FipiLoader
from learning.models import Task, Subject

logger = logging.getLogger(__name__)


class AutoUpdater:
    """Автоматическое обновление материалов"""

    def __init__(self):
        self.is_running = False
        self.thread = None
        self.fipi_loader = FipiLoader()

    def start_scheduler(self):
        """Запускает планировщик обновлений"""
        if self.is_running:
            logger.info("Планировщик уже запущен")
            return

        self.is_running = True
        logger.info("🚀 Запуск планировщика автообновлений...")

        # Расписание обновлений
        schedule.every().day.at("03:00").do(self.daily_update)  # Ежедневно в 3:00
        schedule.every().sunday.at("02:00").do(
            self.weekly_update)  # Еженедельно в воскресенье в 2:00
        schedule.every().day.at("04:00").do(self.generate_voices_batch)  # Генерация голосов в 4:00
        schedule.every(30).minutes.do(self.cleanup_old_data)  # Очистка каждые 30 минут

        # Запускаем в отдельном потоке
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()

        logger.info("✅ Планировщик запущен")

    def stop_scheduler(self):
        """Останавливает планировщик"""
        self.is_running = False
        schedule.clear()
        logger.info("🛑 Планировщик остановлен")

    def _run_scheduler(self):
        """Запускает планировщик в отдельном потоке"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Проверяем каждую минуту
            except Exception as e:
                logger.error(f"Ошибка в планировщике: {str(e)}")
                time.sleep(300)  # При ошибке ждем 5 минут

    def daily_update(self):
        """Ежедневное обновление материалов"""
        logger.info("📅 Начинаем ежедневное обновление материалов...")

        try:
            # Загружаем новые материалы с ФИПИ
            subjects_count, tasks_count = self.fipi_loader.load_subjects()

            if tasks_count > 0:
                logger.info(f"✅ Загружено новых заданий: {tasks_count}")

                # Отправляем уведомление админу
                self._send_admin_notification(
                    f"📚 Ежедневное обновление ExamFlow\n"
                    f"Новых заданий: {tasks_count}\n"
                    f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                )
            else:
                logger.info("ℹ️ Новых материалов не найдено")

        except Exception as e:
            logger.error(f"❌ Ошибка ежедневного обновления: {str(e)}")
            self._send_admin_notification(
                f"❌ Ошибка обновления ExamFlow\n"
                f"Ошибка: {str(e)}\n"
                f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )

    def weekly_update(self):
        """Еженедельное полное обновление"""
        logger.info("📅 Начинаем еженедельное полное обновление...")

        try:
            # Полная перезагрузка данных
            call_command('load_fipi_data')

            # Генерируем голосовые файлы для новых заданий
            self.generate_voices_batch()

            # Очищаем старые данные
            self.cleanup_old_data()

            # Статистика
            total_subjects = Subject.objects.count()
            total_tasks = Task.objects.filter(is_active=True).count()

            logger.info("✅ Еженедельное обновление завершено")

            self._send_admin_notification(
                f"📊 Еженедельное обновление ExamFlow\n"
                f"Всего предметов: {total_subjects}\n"
                f"Всего заданий: {total_tasks}\n"
                f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )

        except Exception as e:
            logger.error(f"❌ Ошибка еженедельного обновления: {str(e)}")
            self._send_admin_notification(
                f"❌ Ошибка еженедельного обновления\n"
                f"Ошибка: {str(e)}\n"
                f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )

    def generate_voices_batch(self):
        """Генерирует голосовые файлы пакетами"""
        logger.info("🎤 Начинаем генерацию голосовых файлов...")

        try:
            # Генерируем голоса для заданий без аудио (максимум 20 за раз)
            tasks_without_audio = Task.objects.filter(
                is_active=True,
                audio_file__isnull=True
            )[:20]

            if not tasks_without_audio:
                logger.info("ℹ️ Все активные задания уже имеют голосовые файлы")
                return

            generated_count = 0

            for task in tasks_without_audio:
                try:
                    from core.voice_service import voice_service
                    result = voice_service.generate_task_audio(task)

                    if result and result['task_audio']:
                        generated_count += 1
                        logger.info(f"🎤 Создан голос для: {task.title}")

                    # Пауза между генерациями
                    time.sleep(2)

                except Exception as e:
                    logger.error(f"Ошибка генерации голоса для {task.id}: {str(e)}")
                    continue

            logger.info(f"✅ Сгенерировано голосовых файлов: {generated_count}")

            if generated_count > 0:
                self._send_admin_notification(
                    f"🎤 Генерация голосов ExamFlow\n"
                    f"Создано файлов: {generated_count}\n"
                    f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                )

        except Exception as e:
            logger.error(f"❌ Ошибка генерации голосов: {str(e)}")

    def cleanup_old_data(self):
        """Очищает старые данные"""
        try:
            # Очищаем старые голосовые файлы (старше 30 дней)
            from core.voice_service import voice_service
            deleted_audio = voice_service.cleanup_old_audio(days=30)

            # Деактивируем очень старые задания (старше 1 года)
            cutoff_date = timezone.now() - timedelta(days=365)
            old_tasks = Task.objects.filter(
                created_at__lt=cutoff_date,
                is_active=True
            )

            deactivated_count = old_tasks.count()
            if deactivated_count > 0:
                old_tasks.update(is_active=False)
                logger.info(f"🗑️ Деактивировано старых заданий: {deactivated_count}")

            if deleted_audio > 0 or deactivated_count > 0:
                logger.info(
                    f"🧹 Очистка: удалено аудио {deleted_audio}, деактивировано заданий {deactivated_count}")

        except Exception as e:
            logger.error(f"❌ Ошибка очистки данных: {str(e)}")

    def _send_admin_notification(self, message):
        """Отправляет уведомление админу"""
        try:
            admin_chat_id = getattr(settings, 'ADMIN_CHAT_ID', None)
            bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)

            if not admin_chat_id or not bot_token:
                logger.warning("Не настроены данные для уведомлений админа")
                return

            import requests

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': admin_chat_id,
                'text': f"🤖 ExamFlow AutoUpdater\n\n{message}",
                'parse_mode': 'HTML'
            }

            response = requests.post(url, data=data, timeout=10)

            if response.status_code == 200:
                logger.info("✅ Уведомление админу отправлено")
            else:
                logger.warning(
                    f"⚠️ Ошибка отправки уведомления: {response.status_code}")

        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления: {str(e)}")

    def manual_update(self):
        """Ручное обновление материалов"""
        logger.info("🔄 Запуск ручного обновления...")

        try:
            subjects_count, tasks_count = self.fipi_loader.load_subjects()

            # Добавляем примеры заданий
            sample_tasks = self.fipi_loader.create_sample_tasks()

            logger.info("✅ Ручное обновление завершено")
            logger.info(
                f"📊 Предметов: {subjects_count}, Заданий: {tasks_count}, Примеров: {sample_tasks}")

            return {
                'subjects': subjects_count,
                'tasks': tasks_count,
                'samples': sample_tasks
            }

        except Exception as e:
            logger.error(f"❌ Ошибка ручного обновления: {str(e)}")
            raise


# Глобальный экземпляр обновлятора
auto_updater = AutoUpdater()


def start_auto_updater():
    """Запускает автообновления"""
    logger.info("🚀 Инициализация системы автообновлений...")
    auto_updater.start_scheduler()
    logger.info("✅ Система автообновлений запущена")


def stop_auto_updater():
    """Останавливает автообновления"""
    auto_updater.stop_scheduler()
    logger.info("🛑 Система автообновлений остановлена")
