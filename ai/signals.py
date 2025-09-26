from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import AiRequest, AiLimit, AiProvider
import logging

logger = logging.getLogger(__name__)

# ========================================
# СИГНАЛЫ ДЛЯ АВТОМАТИЧЕСКОГО СОЗДАНИЯ ЛИМИТОВ
# ========================================

# Получаем модель пользователя безопасно (apps уже готовы внутри AppConfig.ready)
User = get_user_model()

@receiver(post_save, sender=User)
def create_ai_limits_for_new_user(sender, instance, created, **kwargs):
    """Автоматически создает лимиты ИИ для нового пользователя"""
    if created:
        try:
            # Создаем дневной лимит
            AiLimit.objects.create(  # type: ignore[attr-defined]
                user=instance,
                limit_type='daily',
                max_limit=30,  # 30 запросов в день для зарегистрированных
                current_usage=0,
                reset_date=timezone.now() + timedelta(days=1)
            )

            # Создаем месячный лимит
            AiLimit.objects.create(  # type: ignore[attr-defined]
                user=instance,
                limit_type='monthly',
                max_limit=300,  # 300 запросов в месяц
                current_usage=0,
                reset_date=timezone.now() + timedelta(days=30)
            )

            logger.info(f"Созданы лимиты ИИ для пользователя {instance.username}")

        except Exception as e:
            logger.error(
                f"Ошибка при создании лимитов ИИ для пользователя {instance.username}: {e}")

# ========================================
# СИГНАЛЫ ДЛЯ ОБНОВЛЕНИЯ СТАТИСТИКИ ПРОВАЙДЕРОВ
# ========================================

@receiver(post_save, sender=AiRequest)
def update_provider_statistics(sender, instance, **kwargs):
    """Обновляет статистику провайдера ИИ после каждого запроса"""
    # Временно отключаем обновление статистики провайдера
    # так как у AiRequest нет поля provider
    # TODO: Добавить поле provider в модель или переработать логику

# ========================================
# СИГНАЛЫ ДЛЯ ОЧИСТКИ УСТАРЕВШИХ ДАННЫХ
# ========================================

@receiver(post_save, sender=AiLimit)
def check_and_reset_limits(sender, instance, **kwargs):
    """Проверяет и сбрасывает лимиты при необходимости"""
    try:
        if instance.reset_date <= timezone.now():
            # Сбрасываем лимит
            instance.current_usage = 0

            # Устанавливаем новую дату сброса
            if instance.limit_type == 'daily':
                instance.reset_date = timezone.now() + timedelta(days=1)
            elif instance.limit_type == 'monthly':
                instance.reset_date = timezone.now() + timedelta(days=30)

            instance.save()
            logger.info(
                f"Сброшен лимит {instance.limit_type} для пользователя {instance.user.username}")

    except Exception:
        logger.error("Ошибка при сбросе лимита: {e}")

# ========================================
# СИГНАЛЫ ДЛЯ ЛОГИРОВАНИЯ
# ========================================

@receiver(post_save, sender=AiRequest)
def log_ai_request(sender, instance, created, **kwargs):
    """Логирует создание нового запроса к ИИ"""
    if created:
        user_info = instance.user.username if instance.user else f"Session: {instance.session_id}"
        logger.info(f"Новый запрос к ИИ от {user_info}: {instance.request_type}")

@receiver(post_delete, sender=AiRequest)
def log_ai_request_deletion(sender, instance, **kwargs):
    """Логирует удаление запроса к ИИ"""
    user_info = instance.user.username if instance.user else f"Session: {instance.session_id}"
    logger.info(f"Удален запрос к ИИ от {user_info}: {instance.request_type}")

# ========================================
# СИГНАЛЫ ДЛЯ УПРАВЛЕНИЯ КЭШЕМ
# ========================================

@receiver(post_save, sender=AiProvider)
def clear_ai_cache_on_provider_update(sender, instance, **kwargs):
    """Очищает кэш ИИ при обновлении провайдера"""
    try:
        # Здесь можно добавить логику очистки кэша
        # Например, очистка Redis кэша или файлового кэша
        logger.info(f"Кэш ИИ очищен после обновления провайдера {instance.name}")

    except Exception:
        logger.error("Ошибка при очистке кэша ИИ: {e}")

# ========================================
# СИГНАЛЫ ДЛЯ МОНИТОРИНГА
# ========================================

@receiver(post_save, sender=AiRequest)
def check_rate_limiting(sender, instance, **kwargs):
    """Проверяет превышение лимитов и логирует предупреждения"""
    if instance.user:
        try:
            daily_limit = AiLimit.objects.filter(  # type: ignore[attr-defined]
                user=instance.user,
                limit_type='daily'
            ).first()

            if daily_limit and daily_limit.is_exceeded():
                logger.warning(
                    f"Пользователь {instance.user.username} превысил дневной лимит ИИ "
                    f"({daily_limit.current_usage}/{daily_limit.max_limit})"
                )

        except Exception:
            logger.error("Ошибка при проверке лимитов: {e}")

# ========================================
# СИГНАЛЫ ДЛЯ АВТОМАТИЧЕСКОГО ВОССТАНОВЛЕНИЯ
# ========================================

@receiver(post_save, sender=AiProvider)
def auto_reactivate_provider(sender, instance, **kwargs):
    """Автоматически реактивирует провайдера при улучшении статистики"""
    try:
        if not instance.is_active and instance.success_rate > 80:
            instance.is_active = True
            instance.save()
            logger.info("Провайдер {instance.name} автоматически реактивирован")

    except Exception:
        logger.error("Ошибка при автоматической реактивации провайдера: {e}")
