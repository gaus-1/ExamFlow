"""
Кастомные backends для аутентификации
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class EmailBackend(ModelBackend):
    """Backend для аутентификации по email"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """Аутентификация по email и паролю"""
        if username is None:
            username = kwargs.get('username')
        if username is None or password is None:
            return None

        try:
            # Ищем пользователя по email
            user = User.objects.get(email=username)  # type: ignore
            if user.check_password(password):
                return user
        except User.DoesNotExist:  # type: ignore
            return None

        return None

    def get_user(self, user_id):
        """Получение пользователя по ID"""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:  # type: ignore
            return None
