"""
Команда для инициализации freemium лимитов
"""

from django.core.management.base import BaseCommand
from core.freemium.models import SubscriptionLimit


class Command(BaseCommand):
    help = 'Инициализирует freemium лимиты для системы'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Пересоздать лимиты, даже если они уже существуют'
        )
    
    def handle(self, *args, **options):
        force = options['force']
        
        self.stdout.write("🚀 Инициализация freemium лимитов...")
        
        # Проверяем, существуют ли уже лимиты
        if SubscriptionLimit.objects.exists() and not force: # type: ignore
            self.stdout.write(self.style.WARNING("Лимиты уже существуют. Используйте --force для пересоздания.")) # type: ignore        
            return
        
        if force:
            self.stdout.write("🗑️ Удаляем существующие лимиты...")
            SubscriptionLimit.objects.all().delete() # type: ignore
        
        # Создаем бесплатный лимит
        free_limit, created = SubscriptionLimit.objects.get_or_create( # type: ignore
            name='free',
            defaults={
                'daily_ai_requests': 10,
                'max_subjects': 5,
                'max_tasks_per_day': 50,
                'has_analytics': True,
                'has_gamification': True,
                'has_ai_hints': True,
                'is_premium': False,
                'price': 0,
                'description': 'Бесплатный доступ с ограничением запросов'
            }
        )
        
        if created:
            self.stdout.write("✅ Создан бесплатный лимит")
        else:
            self.stdout.write("ℹ️ Бесплатный лимит уже существует")
        
        # Создаем премиум лимит
        premium_limit, created = SubscriptionLimit.objects.get_or_create( # type: ignore
            name='premium',
            defaults={
                'daily_ai_requests': -1,  # -1 означает безлимит
                'max_subjects': -1,
                'max_tasks_per_day': -1,
                'has_analytics': True,
                'has_gamification': True,
                'has_ai_hints': True,
                'is_premium': True,
                'price': 990,
                'description': 'Безлимитный доступ'
            }
        )
        
        if created:
            self.stdout.write("✅ Создан премиум лимит")
        else:
            self.stdout.write("ℹ️ Премиум лимит уже существует")
        
        # Показываем созданные лимиты
        self.stdout.write("\n📊 Созданные лимиты:")
        for limit in SubscriptionLimit.objects.all(): # type: ignore
            self.stdout.write(f"   - {limit.name}: {limit.description}")
            self.stdout.write(f"     AI запросов в день: {limit.daily_ai_requests}")
            self.stdout.write(f"     Цена: {limit.price} ₽")
        
        self.stdout.write(self.style.SUCCESS("\n✅ Инициализация freemium лимитов завершена")) # type: ignore