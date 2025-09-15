"""
Сервис для генерации голосовых подсказок и озвучивания заданий
Использует gTTS (Google Text-to-Speech) для минимальных затрат
"""

import os
import hashlib
import logging
from django.conf import settings
from django.core.cache import cache
from gtts import gTTS
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

class VoiceService:
    """Сервис для работы с голосовыми подсказками"""

    def __init__(self):
        self.cache_timeout = 86400 * 7  # 7 дней кэширования
        self.audio_format = 'mp3'
        self.language = 'ru'
        self.slow_speed = False

        # Создаем директорию для аудио если её нет
        self.audio_dir = Path(settings.MEDIA_ROOT) / 'audio'
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    def text_to_speech(self, text, task_id=None, voice_type='task'):
        """
        Преобразует текст в речь и возвращает путь к файлу

        Args:
            text (str): Текст для озвучивания
            task_id (int): ID задания для кэширования
            voice_type (str): Тип озвучивания (task, solution, hint)

        Returns:
            str: Относительный путь к аудиофайлу или None при ошибке
        """
        try:
            # Создаем уникальный хеш для кэширования
            text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            cache_key = "voice_{voice_type}_{text_hash}"

            # Проверяем кэш
            cached_path = cache.get(cache_key)
            if cached_path and os.path.exists(
                os.path.join(
                    settings.MEDIA_ROOT,
                    cached_path)):
                logger.info("Используем кэшированный аудиофайл: {cached_path}")
                return cached_path

            # Очищаем текст для лучшего озвучивания
            clean_text = self._clean_text_for_speech(text)

            if not clean_text.strip():
                logger.warning("Пустой текст после очистки")
                return None

            # Генерируем аудио
            tts = gTTS(
                text=clean_text,
                lang=self.language,
                slow=self.slow_speed
            )

            # Сохраняем в временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tts.save(tmp_file.name)

                # Создаем финальный путь
                filename = "{voice_type}_{text_hash}.mp3"
                audio_path = self.audio_dir / filename
                relative_path = "audio/{filename}"

                # Перемещаем файл в медиа директорию
                os.rename(tmp_file.name, str(audio_path))

                # Кэшируем путь
                cache.set(cache_key, relative_path, self.cache_timeout)

                logger.info("Создан аудиофайл: {relative_path}")
                return relative_path

        except Exception as e:
            logger.error("Ошибка генерации аудио: {str(e)}")
            return None

    def _clean_text_for_speech(self, text):
        """Очищает текст для лучшего озвучивания"""
        if not text:
            return ""

        # Убираем HTML теги
        import re
        text = re.sub(r'<[^>]+>', '', text)

        # Заменяем математические символы на слова
        replacements = {
            '√': 'корень из ',
            '²': ' в квадрате',
            '³': ' в кубе',
            '≤': ' меньше или равно ',
            '≥': ' больше или равно ',
            '≠': ' не равно ',
            '∞': ' бесконечность',
            '±': ' плюс минус ',
            '×': ' умножить на ',
            '÷': ' разделить на ',
            'π': ' пи ',
            'α': ' альфа ',
            'β': ' бета ',
            'γ': ' гамма ',
            'θ': ' тета ',
            'φ': ' фи ',
            '∆': ' дельта ',
            '∑': ' сумма ',
            '∫': ' интеграл ',
            '°': ' градусов',
            '%': ' процентов',
        }

        for symbol, word in replacements.items():
            text = text.replace(symbol, word)

        # Заменяем числа с дробями
        text = re.sub(r'(\d+)/(\d+)', r'\1 дробь \2', text)

        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()

        # Ограничиваем длину (gTTS имеет лимиты)
        if len(text) > 5000:
            text = text[:5000] + "..."

        return text

    def generate_task_audio(self, task):
        """Генерирует аудио для задания"""
        try:
            # Озвучиваем условие задания
            task_text = "Задание по предмету {task.subject.name}. {task.title}. {task.description}"
            task_audio = self.text_to_speech(task_text, task.id, 'task')

            # Озвучиваем решение если есть
            solution_audio = None
            if task.solution:
                solution_text = "Решение. {task.solution}"
                solution_audio = self.text_to_speech(solution_text, task.id, 'solution')

            # Обновляем модель задания
            if task_audio:
                task.audio_file = task_audio
                task.save()
                logger.info("Аудио для задания {task.id} сохранено")

            return {
                'task_audio': task_audio,
                'solution_audio': solution_audio
            }

        except Exception as e:
            logger.error("Ошибка генерации аудио для задания {task.id}: {str(e)}")
            return None

    def generate_hint_audio(self, hint_text):
        """Генерирует аудио для подсказки"""
        hint_text = "Подсказка. {hint_text}"
        return self.text_to_speech(hint_text, voice_type='hint')

    def cleanup_old_audio(self, days=30):
        """Удаляет старые аудиофайлы"""
        try:
            import time
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            deleted_count = 0

            for audio_file in self.audio_dir.glob('*.mp3'):
                if audio_file.stat().st_mtime < cutoff_time:
                    audio_file.unlink()
                    deleted_count += 1

            logger.info("Удалено старых аудиофайлов: {deleted_count}")
            return deleted_count

        except Exception as e:
            logger.error("Ошибка очистки аудиофайлов: {str(e)}")
            return 0

    def get_audio_url(self, relative_path):
        """Возвращает полный URL аудиофайла"""
        if not relative_path:
            return None
        return "{settings.MEDIA_URL}{relative_path}"

# Глобальный экземпляр сервиса
voice_service = VoiceService()

def generate_task_voices():
    """Генерирует голосовые файлы для всех активных заданий"""
    from learning.models import Task

    logger.info("Начинаем генерацию голосовых файлов...")

    tasks = Task.objects.filter(is_active=True, audio_file__isnull=True)[  # type: ignore
        :50]  # Ограничиваем для экономии
    generated_count = 0

    for task in tasks:
        try:
            result = voice_service.generate_task_audio(task)
            if result and result['task_audio']:
                generated_count += 1
                logger.info("Аудио создано для задания: {task.title}")

            # Пауза между генерациями для экономии ресурсов
            import time
            time.sleep(1)

        except Exception as e:
            logger.error("Ошибка генерации аудио для {task.id}: {str(e)}")
            continue

    logger.info("Генерация завершена. Создано аудиофайлов: {generated_count}")
    return generated_count
