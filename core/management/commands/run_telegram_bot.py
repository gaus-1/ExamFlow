"""
Команда для запуска Telegram бота
"""

import logging
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):  # type: ignore
    help = "Запускает Telegram бота с базовыми командами"

    def add_arguments(self, parser):
        parser.add_argument(
            '--webhook',
            action='store_true',
            help='Запустить в режиме webhook вместо polling'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🤖 Запуск Telegram бота...')  # type: ignore
        )

        try:
            import asyncio
            from telegram import Update
            from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
            from core.rag_system.orchestrator import RAGOrchestrator

            # Получаем токен бота
            bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
            if not bot_token:
                self.stdout.write(
                    self.style.ERROR('❌ TELEGRAM_BOT_TOKEN не настроен в settings')  # type: ignore
                )
                return

            # Инициализируем оркестратор
            orchestrator = RAGOrchestrator()

            async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
                """Обработчик команды /start"""
                await update.message.reply_text(
                    "👋 Привет! Я AI-помощник ExamFlow.\n\n"
                    "Доступные команды:\n"
                    "/search <запрос> - поиск по материалам ФИПИ\n"
                    "/fipi <предмет> <тип> - поиск по конкретному предмету\n"
                    "/help - помощь\n\n"
                    "Просто напишите вопрос, и я помогу с подготовкой к ЕГЭ/ОГЭ!"
                )

            async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
                """Обработчик команды /help"""
                await update.message.reply_text(
                    "📚 Помощь по командам:\n\n"
                    "/search <запрос> - поиск по всем материалам ФИПИ\n"
                    "Пример: /search как решать квадратные уравнения\n\n"
                    "/fipi <предмет> <тип> - поиск по конкретному предмету\n"
                    "Предметы: математика, русский\n"
                    "Типы: demo_variant, codifier, specification\n"
                    "Пример: /fipi математика demo_variant\n\n"
                    "Также можете просто написать вопрос в чат!"
                )

            async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
                """Обработчик команды /search"""
                query = ' '.join(context.args) if context.args else ''
                if not query:
                    await update.message.reply_text(
                        "❌ Укажите запрос для поиска.\n"
                        "Пример: /search как решать квадратные уравнения"
                    )
                    return

                await update.message.reply_text("🔍 Ищу информацию...")
                
                try:
                    result = orchestrator.process_query(query=query)
                    
                    if result.get('answer'):
                        response = f"🤖 {result['answer']}\n\n"
                        if result.get('sources'):
                            response += "📚 Источники:\n"
                            for source in result['sources'][:3]:  # Показываем только первые 3
                                response += f"• {source.get('title', 'Без названия')}\n"
                        
                        await update.message.reply_text(response)
                    else:
                        await update.message.reply_text(
                            "😔 Не удалось найти релевантную информацию по вашему запросу."
                        )
                        
                except Exception as e:
                    logger.error(f"Ошибка в search_command: {e}")
                    await update.message.reply_text(
                        "❌ Произошла ошибка при поиске. Попробуйте позже."
                    )

            async def fipi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
                """Обработчик команды /fipi"""
                if len(context.args) < 2:
                    await update.message.reply_text(
                        "❌ Укажите предмет и тип документа.\n"
                        "Пример: /fipi математика demo_variant"
                    )
                    return

                subject = context.args[0].lower()
                doc_type = context.args[1].lower()
                
                # Маппинг предметов
                subject_map = {
                    'математика': 'Математика',
                    'матем': 'Математика',
                    'math': 'Математика',
                    'русский': 'Русский язык',
                    'русский язык': 'Русский язык',
                    'russian': 'Русский язык'
                }
                
                mapped_subject = subject_map.get(subject, subject.title())
                
                await update.message.reply_text(f"🔍 Ищу по предмету: {mapped_subject}, тип: {doc_type}")
                
                try:
                    result = orchestrator.process_query(
                        query="материалы для подготовки",
                        subject=mapped_subject,
                        document_type=doc_type
                    )
                    
                    if result.get('answer'):
                        response = f"📖 {result['answer']}\n\n"
                        if result.get('sources'):
                            response += "📚 Найденные материалы:\n"
                            for source in result['sources'][:3]:
                                response += f"• {source.get('title', 'Без названия')}\n"
                        
                        await update.message.reply_text(response)
                    else:
                        await update.message.reply_text(
                            f"😔 Материалы по предмету '{mapped_subject}' и типу '{doc_type}' не найдены."
                        )
                        
                except Exception as e:
                    logger.error(f"Ошибка в fipi_command: {e}")
                    await update.message.reply_text(
                        "❌ Произошла ошибка при поиске. Попробуйте позже."
                    )

            async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
                """Обработчик обычных сообщений"""
                query = update.message.text
                if not query:
                    return

                await update.message.reply_text("🤔 Обрабатываю ваш вопрос...")
                
                try:
                    result = orchestrator.process_query(query=query)
                    
                    if result.get('answer'):
                        response = f"💡 {result['answer']}\n\n"
                        if result.get('sources'):
                            response += "📚 Источники:\n"
                            for source in result['sources'][:2]:
                                response += f"• {source.get('title', 'Без названия')}\n"
                        
                        await update.message.reply_text(response)
                    else:
                        await update.message.reply_text(
                            "😔 Не удалось найти релевантную информацию. "
                            "Попробуйте переформулировать вопрос или используйте команду /search"
                        )
                        
                except Exception as e:
                    logger.error(f"Ошибка в handle_message: {e}")
                    await update.message.reply_text(
                        "❌ Произошла ошибка при обработке запроса. Попробуйте позже."
                    )

            async def main():
                """Основная функция запуска бота"""
                # Создаем приложение
                application = Application.builder().token(bot_token).build()

                # Добавляем обработчики
                application.add_handler(CommandHandler("start", start))
                application.add_handler(CommandHandler("help", help_command))
                application.add_handler(CommandHandler("search", search_command))
                application.add_handler(CommandHandler("fipi", fipi_command))
                application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

                # Запускаем бота
                if options['webhook']:
                    self.stdout.write(
                        self.style.WARNING('⚠️ Webhook режим не реализован, используем polling')  # type: ignore
                    )
                
                self.stdout.write(
                    self.style.SUCCESS('✅ Бот запущен! Нажмите Ctrl+C для остановки.')  # type: ignore
                )
                
                # Запускаем polling
                await application.run_polling()

            # Запускаем бота
            asyncio.run(main())

        except ImportError:
            self.stdout.write(
                self.style.ERROR('❌ python-telegram-bot не установлен. Выполните: pip install python-telegram-bot')  # type: ignore
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при запуске бота: {e}')  # type: ignore
            )
