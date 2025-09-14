"""
Сервисы для Telegram аутентификации ExamFlow
"""

import hashlib
import hmac
import json
import logging
from typing import Dict, Any, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from .models import TelegramUser, TelegramAuthSession, TelegramAuthLog

logger = logging.getLogger(__name__)


class TelegramAuthService:
    """Сервис для аутентификации через Telegram Login Widget"""
    
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN не настроен в settings")
    
    def verify_telegram_data(self, auth_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Проверяет подлинность данных от Telegram Login Widget
        
        Args:
            auth_data: Данные от Telegram (id, first_name, username, hash, auth_date)
            
        Returns:
            Tuple[bool, str]: (успех_проверки, сообщение_об_ошибке)
        """
        try:
            # Извлекаем hash из данных
            received_hash = auth_data.pop('hash', None)
            if not received_hash:
                return False, "Отсутствует hash в данных аутентификации"
            
            # Проверяем обязательные поля
            required_fields = ['id', 'first_name', 'auth_date']
            for field in required_fields:
                if field not in auth_data:
                    return False, f"Отсутствует обязательное поле: {field}"
            
            # Создаем секретный ключ из токена бота
            secret_key = hashlib.sha256(self.bot_token.encode()).digest()
            
            # Формируем строку для проверки
            data_check_string = self._create_data_check_string(auth_data)
            
            # Вычисляем hash
            calculated_hash = hmac.new(
                secret_key,
                data_check_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Сравниваем hash
            if not hmac.compare_digest(received_hash, calculated_hash):
                return False, "Неверный hash - данные могли быть подделаны"
            
            # Проверяем время аутентификации (не старше 24 часов)
            auth_date = int(auth_data['auth_date'])
            current_time = int(timezone.now().timestamp())
            if current_time - auth_date > 86400:  # 24 часа
                return False, "Данные аутентификации устарели"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Ошибка проверки данных Telegram: {e}")
            return False, f"Ошибка проверки данных: {str(e)}"
    
    def _create_data_check_string(self, auth_data: Dict[str, Any]) -> str:
        """
        Создает строку для проверки hash согласно документации Telegram
        
        Args:
            auth_data: Данные аутентификации
            
        Returns:
            str: Строка для проверки
        """
        # Сортируем ключи и создаем строку вида "key=value\nkey=value"
        sorted_items = sorted(auth_data.items())
        return '\n'.join([f"{key}={value}" for key, value in sorted_items])
    
    @transaction.atomic
    def authenticate_user(self, auth_data: Dict[str, Any], 
                         ip_address: str = None, 
                         user_agent: str = None) -> Tuple[bool, Optional[TelegramUser], str]:
        """
        Аутентифицирует пользователя через Telegram данные
        
        Args:
            auth_data: Данные от Telegram
            ip_address: IP адрес пользователя
            user_agent: User Agent браузера
            
        Returns:
            Tuple[bool, TelegramUser, str]: (успех, пользователь, сообщение)
        """
        try:
            # Проверяем данные
            is_valid, error_message = self.verify_telegram_data(auth_data.copy())
            if not is_valid:
                self._log_auth_attempt(
                    int(auth_data.get('id', 0)), 
                    False, 
                    ip_address, 
                    user_agent, 
                    error_message
                )
                return False, None, error_message
            
            telegram_id = int(auth_data['id'])
            
            # Получаем или создаем пользователя
            user, created = TelegramUser.objects.get_or_create(
                telegram_id=telegram_id,
                defaults={
                    'telegram_username': auth_data.get('username', ''),
                    'telegram_first_name': auth_data.get('first_name', ''),
                    'telegram_last_name': auth_data.get('last_name', ''),
                    'language_code': auth_data.get('language_code', 'ru'),
                    'last_login': timezone.now()
                }
            )
            
            # Обновляем данные существующего пользователя
            if not created:
                user.telegram_username = auth_data.get('username', '')
                user.telegram_first_name = auth_data.get('first_name', '')
                user.telegram_last_name = auth_data.get('last_name', '')
                user.language_code = auth_data.get('language_code', 'ru')
                user.last_login = timezone.now()
                user.save()
            
            # Создаем сессию
            session = self._create_auth_session(user, ip_address, user_agent)
            
            # Логируем успешную аутентификацию
            self._log_auth_attempt(telegram_id, True, ip_address, user_agent)
            
            message = f"✅ Добро пожаловать, {user.display_name}!"
            if created:
                message += "\n\n🎉 Ваш аккаунт успешно создан!"
            
            return True, user, message
            
        except Exception as e:
            logger.error(f"Ошибка аутентификации пользователя: {e}")
            error_message = f"Ошибка аутентификации: {str(e)}"
            self._log_auth_attempt(
                int(auth_data.get('id', 0)), 
                False, 
                ip_address, 
                user_agent, 
                error_message
            )
            return False, None, error_message
    
    def _create_auth_session(self, user: TelegramUser, 
                           ip_address: str = None, 
                           user_agent: str = None) -> TelegramAuthSession:
        """Создает сессию аутентификации"""
        import secrets
        
        session_token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timezone.timedelta(days=30)  # 30 дней
        
        session = TelegramAuthSession.objects.create(
            user=user,
            session_token=session_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return session
    
    def _log_auth_attempt(self, telegram_id: int, success: bool, 
                         ip_address: str = None, user_agent: str = None, 
                         error_message: str = None):
        """Логирует попытку аутентификации"""
        TelegramAuthLog.objects.create(
            telegram_id=telegram_id,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=error_message or ''
        )
    
    def get_user_by_session(self, session_token: str) -> Optional[TelegramUser]:
        """Получает пользователя по токену сессии"""
        try:
            session = TelegramAuthSession.objects.select_related('user').get(
                session_token=session_token,
                is_active=True
            )
            
            if session.is_expired:
                session.is_active = False
                session.save()
                return None
            
            return session.user
            
        except TelegramAuthSession.DoesNotExist:
            return None
    
    def logout_user(self, session_token: str) -> bool:
        """Завершает сессию пользователя"""
        try:
            session = TelegramAuthSession.objects.get(session_token=session_token)
            session.is_active = False
            session.save()
            return True
        except TelegramAuthSession.DoesNotExist:
            return False


# Глобальный экземпляр сервиса
telegram_auth_service = TelegramAuthService()
