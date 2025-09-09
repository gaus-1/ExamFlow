#!/usr/bin/env python3
"""
Скрипт для поддержания активности базы данных PostgreSQL
Предотвращает "засыпание" базы данных из-за неактивности
"""

import os
import time
import logging
import psycopg2
from datetime import datetime
import schedule
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_keepalive.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DatabaseKeepAlive:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.connection = None
        self.last_ping = None
        self.ping_interval = 300  # 5 минут
        self.max_retries = 3
        
    def get_connection(self):
        """Получение соединения с базой данных"""
        try:
            if self.connection is None or self.connection.closed:
                self.connection = psycopg2.connect(self.db_url)
                logger.info("Соединение с базой данных установлено")
            
            return self.connection
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            return None
    
    def ping_database(self):
        """Пинг базы данных для поддержания активности"""
        try:
            conn = self.get_connection()
            if conn is None:
                logger.error("Нет соединения с базой данных")
                return False
            
            # Выполняем простой запрос
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                if result and result[0] == 1:
                    self.last_ping = datetime.now()
                    logger.info("Пинг базы данных успешен")
                    return True
                else:
                    logger.warning("Неожиданный результат пинга")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка при пинге базы данных: {e}")
            self.close_connection()
            return False
    
    def execute_keepalive_query(self):
        """Выполнение запроса для поддержания активности"""
        try:
            conn = self.get_connection()
            if conn is None:
                return False
            
            with conn.cursor() as cursor:
                # Простой запрос, который не нагружает базу
                cursor.execute("""
                    SELECT 
                        current_timestamp,
                        version(),
                        current_database(),
                        current_user
                """)
                
                result = cursor.fetchone()
                if result:
                    logger.info(f"Keep-alive запрос выполнен: {result[0]}")
                    return True
                    
        except Exception as e:
            logger.error(f"Ошибка keep-alive запроса: {e}")
            return False
        
        return False
    
    def check_database_health(self):
        """Проверка здоровья базы данных"""
        try:
            conn = self.get_connection()
            if conn is None:
                return False
            
            with conn.cursor() as cursor:
                # Проверяем активные соединения
                cursor.execute("""
                    SELECT 
                        count(*) as active_connections,
                        max(backend_start) as oldest_connection
                    FROM pg_stat_activity 
                    WHERE state = 'active'
                """)
                
                connections = cursor.fetchone()
                if connections:
                    logger.info(f"Активных соединений: {connections[0]}")
                
                # Проверяем размер базы данных
                cursor.execute("""
                    SELECT 
                        pg_size_pretty(pg_database_size(current_database())) as db_size
                """)
                
                size = cursor.fetchone()
                if size:
                    logger.info(f"Размер базы данных: {size[0]}")
                
                return True
                
        except Exception as e:
            logger.error(f"Ошибка проверки здоровья БД: {e}")
            return False
    
    def optimize_connections(self):
        """Оптимизация соединений с базой данных"""
        try:
            conn = self.get_connection()
            if conn is None:
                return False
            
            with conn.cursor() as cursor:
                # Проверяем настройки соединений
                cursor.execute("""
                    SHOW max_connections;
                """)
                
                max_conn = cursor.fetchone()
                if max_conn:
                    logger.info(f"Максимум соединений: {max_conn[0]}")
                
                # Проверяем таймауты
                cursor.execute("""
                    SHOW idle_in_transaction_session_timeout;
                """)
                
                timeout = cursor.fetchone()
                if timeout:
                    logger.info(f"Таймаут неактивных транзакций: {timeout[0]}")
                
                return True
                
        except Exception as e:
            logger.error(f"Ошибка оптимизации соединений: {e}")
            return False
    
    def close_connection(self):
        """Закрывает соединение с базой данных"""
        if self.connection:
            try:
                self.connection.close()
                logger.info("Соединение с базой данных закрыто")
            except Exception as e:
                logger.error(f"Ошибка при закрытии соединения: {e}")
            finally:
                self.connection = None
    
    def run_keepalive_cycle(self):
        """Основной цикл поддержания активности"""
        logger.info("Запуск цикла поддержания активности БД")
        
        # Пинг базы данных
        if self.ping_database():
            # Выполняем keep-alive запрос
            self.execute_keepalive_query()
            
            # Проверяем здоровье каждые 10 минут
            if not self.last_ping or (datetime.now() - self.last_ping).seconds > 600:
                self.check_database_health()
                self.optimize_connections()
        else:
            logger.warning("Пинг не удался, повторная попытка через минуту")
            time.sleep(60)
            self.ping_database()
    
    def start_scheduled_keepalive(self):
        """Запуск запланированного поддержания активности"""
        logger.info("Запуск запланированного поддержания активности БД")
        
        # Пинг каждые 5 минут
        schedule.every(5).minutes.do(self.run_keepalive_cycle)
        
        # Проверка здоровья каждый час
        schedule.every().hour.do(self.check_database_health)
        
        # Оптимизация соединений каждые 2 часа
        schedule.every(2).hours.do(self.optimize_connections)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(30)  # Проверяем каждые 30 секунд
                
        except KeyboardInterrupt:
            logger.info("Остановка по запросу пользователя")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
        finally:
            self.close_connection()
    
    def test_connection(self):
        """Тестирование соединения с базой данных"""
        logger.info("Тестирование соединения с базой данных")
        
        try:
            conn = self.get_connection()
            if conn is None:
                logger.error("Не удалось установить соединение")
                return False
            
            # Тестовый запрос
            with conn.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()
                logger.info(f"Версия PostgreSQL: {version[0]}")
            
            # Проверяем доступные таблицы
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    LIMIT 5
                """)
                
                tables = cursor.fetchall()
                if tables:
                    logger.info(f"Доступные таблицы: {', '.join([t[0] for t in tables])}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка тестирования: {e}")
            return False

def main():
    """Основная функция"""
    logger.info("Запуск системы поддержания активности базы данных")
    
    # Проверяем наличие DATABASE_URL
    if not os.getenv('DATABASE_URL'):
        logger.error("DATABASE_URL не найден в переменных окружения")
        return
    
    # Создаем экземпляр
    keepalive = DatabaseKeepAlive()
    
    # Тестируем соединение
    if not keepalive.test_connection():
        logger.error("Тестирование соединения не удалось")
        return
    
    # Запускаем запланированное поддержание активности
    keepalive.start_scheduled_keepalive()

if __name__ == "__main__":
    main()
