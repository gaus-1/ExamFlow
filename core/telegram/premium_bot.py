"""
Расширенная функциональность Telegram бота для премиум-пользователей
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from django.conf import settings
from django.utils import timezone

from core.premium.access_control import get_access_control, get_usage_tracker
from core.models import FIPIData, DataChunk
from core.rag_system.orchestrator import get_ai_orchestrator

logger = logging.getLogger(__name__)

class PremiumTelegramBot:
    """Расширенная функциональность бота для премиум-пользователей"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.access_control = get_access_control()
        self.usage_tracker = get_usage_tracker()
    
    def handle_premium_command(self, message, user):
        """Обрабатывает команды премиум-пользователей"""
        command = message.text.split()[0].lower()
        
        if command == '/premium':
            return self.show_premium_status(message, user)
        elif command == '/export':
            return self.handle_pdf_export(message, user)
        elif command == '/search':
            return self.handle_advanced_search(message, user)
        elif command == '/recommend':
            return self.handle_recommendations(message, user)
        elif command == '/compare':
            return self.handle_version_comparison(message, user)
        elif command == '/usage':
            return self.show_usage_stats(message, user)
        else:
            return self.show_premium_help(message, user)
    
    def show_premium_status(self, message, user):
        """Показывает статус премиум-подписки"""
        try:
            is_premium = self.access_control.is_premium_user(user)
            has_subscription = self.access_control.has_active_subscription(user)
            features = self.access_control.get_user_features(user)
            
            status_text = "🔒 <b>Статус подписки</b>\n\n"
            
            if is_premium:
                status_text += "✅ <b>Премиум-пользователь</b>\n"
                status_text += f"📅 Подписка: {'Активна' if has_subscription else 'Неактивна'}\n\n"
                
                status_text += "🎯 <b>Доступные функции:</b>\n"
                for feature in features:
                    if feature != 'basic':
                        feature_name = self.get_feature_name(feature)
                        status_text += f"• {feature_name}\n"
            else:
                status_text += "❌ <b>Базовый пользователь</b>\n\n"
                status_text += "💡 <b>Обновитесь до премиум для получения:</b>\n"
                status_text += "• Полного доступа к материалам\n"
                status_text += "• Экспорта в PDF\n"
                status_text += "• Расширенного поиска\n"
                status_text += "• Персональных рекомендаций\n"
                status_text += "• Сравнения версий\n"
                status_text += "• Приоритетной поддержки\n\n"
                status_text += "🚀 <a href='https://examflow.ru/auth/subscribe/'>Оформить подписку</a>"
            
            self.bot.send_message(
                message.chat.id,
                status_text,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logger.error(f"Ошибка показа статуса премиум: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка получения статуса подписки"
            )
    
    def handle_pdf_export(self, message, user):
        """Обрабатывает экспорт в PDF"""
        if not self.access_control.can_access_feature(user, 'pdf_export'):
            self.bot.send_message(
                message.chat.id,
                "🔒 Для экспорта в PDF требуется премиум-подписка\n"
                "🚀 <a href='https://examflow.ru/auth/subscribe/'>Оформить подписку</a>",
                parse_mode='HTML'
            )
            return
        
        try:
            # Парсим аргументы команды
            args = message.text.split()[1:] if len(message.text.split()) > 1 else []
            
            if not args:
                self.bot.send_message(
                    message.chat.id,
                    "📄 <b>Экспорт в PDF</b>\n\n"
                    "Использование: /export [ID_документа]\n"
                    "Пример: /export 123",
                    parse_mode='HTML'
                )
                return
            
            document_id = args[0]
            
            # Проверяем лимиты
            if not self.usage_tracker.track_usage(user, 'pdf_exports', 1):
                self.bot.send_message(
                    message.chat.id,
                    "⚠️ Превышен лимит экспорта в PDF на сегодня"
                )
                return
            
            # Получаем документ
            try:
                fipi_data = FIPIData.objects.get(id=document_id)  # type: ignore
            except FIPIData.DoesNotExist:  # type: ignore
                self.bot.send_message(
                    message.chat.id,
                    "❌ Документ не найден"
                )
                return
            
            # Отправляем сообщение о начале экспорта
            export_msg = self.bot.send_message(
                message.chat.id,
                "📄 Генерирую PDF... Пожалуйста, подождите."
            )
            
            # Здесь должна быть логика генерации PDF
            # Пока отправляем заглушку
            pdf_url = f"https://examflow.ru/api/premium/pdf/{document_id}/download/"
            
            # Обновляем сообщение
            self.bot.edit_message_text(
                f"✅ <b>PDF готов!</b>\n\n"
                f"📄 <b>{fipi_data.title}</b>\n"
                f"🔗 <a href='{pdf_url}'>Скачать PDF</a>",
                message.chat.id,
                export_msg.message_id,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Ошибка экспорта в PDF: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка генерации PDF"
            )
    
    def handle_advanced_search(self, message, user):
        """Обрабатывает расширенный поиск"""
        if not self.access_control.can_access_feature(user, 'advanced_search'):
            self.bot.send_message(
                message.chat.id,
                "🔒 Для расширенного поиска требуется премиум-подписка\n"
                "🚀 <a href='https://examflow.ru/auth/subscribe/'>Оформить подписку</a>",
                parse_mode='HTML'
            )
            return
        
        try:
            # Парсим поисковый запрос
            query = ' '.join(message.text.split()[1:]) if len(message.text.split()) > 1 else ''
            
            if not query:
                self.bot.send_message(
                    message.chat.id,
                    "🔍 <b>Расширенный поиск</b>\n\n"
                    "Использование: /search [запрос]\n"
                    "Пример: /search теория вероятности",
                    parse_mode='HTML'
                )
                return
            
            # Проверяем лимиты
            if not self.usage_tracker.track_usage(user, 'advanced_searches', 1):
                self.bot.send_message(
                    message.chat.id,
                    "⚠️ Превышен лимит расширенного поиска на сегодня"
                )
                return
            
            # Отправляем сообщение о начале поиска
            search_msg = self.bot.send_message(
                message.chat.id,
                f"🔍 Ищу: <b>{query}</b>\n\nПожалуйста, подождите...",
                parse_mode='HTML'
            )
            
            # Выполняем поиск
            orchestrator = get_ai_orchestrator()
            results = orchestrator.search_content(
                query=query,
                user=user,
                limit=5
            )
            
            if not results:
                self.bot.edit_message_text(
                    f"🔍 <b>Поиск: {query}</b>\n\n"
                    "❌ Ничего не найдено",
                    message.chat.id,
                    search_msg.message_id,
                    parse_mode='HTML'
                )
                return
            
            # Формируем результат
            result_text = f"🔍 <b>Результаты поиска: {query}</b>\n\n"
            
            for i, result in enumerate(results[:5], 1):
                title = result.get('title', 'Без названия')
                content = result.get('content', '')[:200] + '...' if len(result.get('content', '')) > 200 else result.get('content', '')
                url = result.get('url', '')
                
                result_text += f"{i}. <b>{title}</b>\n"
                result_text += f"   {content}\n"
                if url:
                    result_text += f"   🔗 <a href='{url}'>Подробнее</a>\n"
                result_text += "\n"
            
            self.bot.edit_message_text(
                result_text,
                message.chat.id,
                search_msg.message_id,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logger.error(f"Ошибка расширенного поиска: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка выполнения поиска"
            )
    
    def handle_recommendations(self, message, user):
        """Обрабатывает персональные рекомендации"""
        if not self.access_control.can_access_feature(user, 'personalized_recommendations'):
            self.bot.send_message(
                message.chat.id,
                "🔒 Для персональных рекомендаций требуется премиум-подписка\n"
                "🚀 <a href='https://examflow.ru/auth/subscribe/'>Оформить подписку</a>",
                parse_mode='HTML'
            )
            return
        
        try:
            # Проверяем лимиты
            if not self.usage_tracker.track_usage(user, 'daily_requests', 1):
                self.bot.send_message(
                    message.chat.id,
                    "⚠️ Превышен дневной лимит запросов"
                )
                return
            
            # Отправляем сообщение о начале генерации рекомендаций
            rec_msg = self.bot.send_message(
                message.chat.id,
                "🎯 Генерирую персональные рекомендации...\nПожалуйста, подождите."
            )
            
            # Получаем рекомендации
            orchestrator = get_ai_orchestrator()
            recommendations = orchestrator.get_personalized_recommendations(
                user=user,
                limit=5
            )
            
            if not recommendations:
                self.bot.edit_message_text(
                    "🎯 <b>Персональные рекомендации</b>\n\n"
                    "❌ Недостаточно данных для генерации рекомендаций",
                    message.chat.id,
                    rec_msg.message_id,
                    parse_mode='HTML'
                )
                return
            
            # Формируем результат
            result_text = "🎯 <b>Персональные рекомендации</b>\n\n"
            
            for i, rec in enumerate(recommendations[:5], 1):
                title = rec.get('title', 'Без названия')
                reason = rec.get('reason', 'Рекомендуется на основе ваших предпочтений')
                url = rec.get('url', '')
                
                result_text += f"{i}. <b>{title}</b>\n"
                result_text += f"   💡 {reason}\n"
                if url:
                    result_text += f"   🔗 <a href='{url}'>Изучить</a>\n"
                result_text += "\n"
            
            self.bot.edit_message_text(
                result_text,
                message.chat.id,
                rec_msg.message_id,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения рекомендаций: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка генерации рекомендаций"
            )
    
    def handle_version_comparison(self, message, user):
        """Обрабатывает сравнение версий"""
        if not self.access_control.can_access_feature(user, 'version_comparison'):
            self.bot.send_message(
                message.chat.id,
                "🔒 Для сравнения версий требуется премиум-подписка\n"
                "🚀 <a href='https://examflow.ru/auth/subscribe/'>Оформить подписку</a>",
                parse_mode='HTML'
            )
            return
        
        try:
            # Парсим аргументы
            args = message.text.split()[1:] if len(message.text.split()) > 1 else []
            
            if len(args) < 2:
                self.bot.send_message(
                    message.chat.id,
                    "🔄 <b>Сравнение версий</b>\n\n"
                    "Использование: /compare [ID_версии_1] [ID_версии_2]\n"
                    "Пример: /compare 123 456",
                    parse_mode='HTML'
                )
                return
            
            version1_id, version2_id = args[0], args[1]
            
            # Проверяем лимиты
            if not self.usage_tracker.track_usage(user, 'daily_requests', 1):
                self.bot.send_message(
                    message.chat.id,
                    "⚠️ Превышен дневной лимит запросов"
                )
                return
            
            # Получаем версии
            try:
                version1 = FIPIData.objects.get(id=version1_id)  # type: ignore
                version2 = FIPIData.objects.get(id=version2_id)  # type: ignore
            except FIPIData.DoesNotExist:  # type: ignore
                self.bot.send_message(
                    message.chat.id,
                    "❌ Одна из версий не найдена"
                )
                return
            
            # Отправляем сообщение о начале сравнения
            comp_msg = self.bot.send_message(
                message.chat.id,
                "🔄 Сравниваю версии... Пожалуйста, подождите."
            )
            
            # Выполняем сравнение
            orchestrator = get_ai_orchestrator()
            comparison = orchestrator.compare_versions(version1, version2)
            
            # Формируем результат
            result_text = f"🔄 <b>Сравнение версий</b>\n\n"
            result_text += f"📄 <b>Версия 1:</b> {version1.title}\n"
            result_text += f"📄 <b>Версия 2:</b> {version2.title}\n\n"
            
            if comparison:
                changes = comparison.get('changes', [])
                if changes:
                    result_text += "📋 <b>Основные изменения:</b>\n"
                    for change in changes[:5]:
                        result_text += f"• {change}\n"
                else:
                    result_text += "✅ Изменений не обнаружено"
            else:
                result_text += "❌ Ошибка сравнения версий"
            
            self.bot.edit_message_text(
                result_text,
                message.chat.id,
                comp_msg.message_id,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Ошибка сравнения версий: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка сравнения версий"
            )
    
    def show_usage_stats(self, message, user):
        """Показывает статистику использования"""
        try:
            actions = ['daily_requests', 'monthly_requests', 'pdf_exports', 'advanced_searches']
            
            stats_text = "📊 <b>Статистика использования</b>\n\n"
            
            for action in actions:
                stats = self.usage_tracker.get_usage_stats(user, action)
                action_name = self.get_action_name(action)
                
                stats_text += f"📈 <b>{action_name}</b>\n"
                stats_text += f"   Использовано: {stats['current']}/{stats['limit']}\n"
                stats_text += f"   Осталось: {stats['remaining']}\n\n"
            
            self.bot.send_message(
                message.chat.id,
                stats_text,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Ошибка показа статистики: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка получения статистики"
            )
    
    def show_premium_help(self, message, user):
        """Показывает справку по премиум-командам"""
        help_text = "🌟 <b>Премиум-команды</b>\n\n"
        
        if self.access_control.is_premium_user(user):
            help_text += "✅ <b>Доступные команды:</b>\n"
            help_text += "• /premium - статус подписки\n"
            help_text += "• /export [ID] - экспорт в PDF\n"
            help_text += "• /search [запрос] - расширенный поиск\n"
            help_text += "• /recommend - персональные рекомендации\n"
            help_text += "• /compare [ID1] [ID2] - сравнение версий\n"
            help_text += "• /usage - статистика использования\n"
        else:
            help_text += "🔒 <b>Премиум-функции:</b>\n"
            help_text += "• Экспорт материалов в PDF\n"
            help_text += "• Расширенный интеллектуальный поиск\n"
            help_text += "• Персональные рекомендации\n"
            help_text += "• Сравнение версий документов\n"
            help_text += "• Неограниченные запросы\n"
            help_text += "• Приоритетная поддержка\n\n"
            help_text += "🚀 <a href='https://examflow.ru/auth/subscribe/'>Оформить подписку</a>"
        
        self.bot.send_message(
            message.chat.id,
            help_text,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    
    def get_feature_name(self, feature: str) -> str:
        """Получает человекочитаемое название функции"""
        feature_names = {
            'premium_content': 'Премиум-контент',
            'pdf_export': 'Экспорт в PDF',
            'advanced_search': 'Расширенный поиск',
            'personalized_recommendations': 'Персональные рекомендации',
            'version_comparison': 'Сравнение версий',
            'unlimited_requests': 'Неограниченные запросы',
            'priority_support': 'Приоритетная поддержка'
        }
        return feature_names.get(feature, feature)
    
    def get_action_name(self, action: str) -> str:
        """Получает человекочитаемое название действия"""
        action_names = {
            'daily_requests': 'Дневные запросы',
            'monthly_requests': 'Месячные запросы',
            'pdf_exports': 'Экспорт в PDF',
            'advanced_searches': 'Расширенный поиск'
        }
        return action_names.get(action, action)
