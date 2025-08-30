"""
Формы для модуля аутентификации

Содержит упрощенные формы в Duolingo-стиле для:
- Регистрации (только имя, email, пароль)
- Входа в систему (email + пароль)
- Обновления профиля
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
# from .models import UserProfile  # UserProfile больше не существует


class TechRegisterForm(UserCreationForm):
    """Упрощенная форма регистрации в Duolingo-стиле - только необходимые поля"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Ваш email адрес',
            'class': 'form-control-duolingo'
        })
    )
    first_name = forms.CharField(
        max_length=30, 
        required=True,  # Теперь обязательное поле
        widget=forms.TextInput(attrs={
            'placeholder': 'Ваше имя',
            'class': 'form-control-duolingo'
        })
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'email', 'password1', 'password2')  # Убрали username, last_name, phone
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Duolingo-стиль оформление полей
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Придумайте пароль',
            'class': 'form-control-duolingo'
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Повторите пароль',
            'class': 'form-control-duolingo'
        })
        
        # Русские подписи полей
        self.fields['first_name'].label = 'Ваше имя'
        self.fields['email'].label = 'Email адрес'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтвердите пароль'
    
    def save(self, commit=True):
        """Сохраняет пользователя с автогенерацией username из email"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        
        # Автоматически генерируем username из email (до @ символа)
        base_username = self.cleaned_data['email'].split('@')[0]
        username = base_username
        
        # Если username уже существует, добавляем цифру
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user.username = username
        
        if commit:
            user.save()
            # UserProfile больше не создается автоматически
        return user


class TechLoginForm(AuthenticationForm):
    """Упрощенная форма входа в Duolingo-стиле - вход по email"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control-duolingo',
            'placeholder': 'Ваш email адрес'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control-duolingo',
            'placeholder': 'Ваш пароль'
        })
        
        # Русские подписи
        self.fields['username'].label = 'Email'
        self.fields['password'].label = 'Пароль'


class ProfileUpdateForm(forms.Form):
    """Форма обновления профиля пользователя"""
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем русские подписи для полей формы
        self.fields['first_name'].label = 'Имя'
        self.fields['last_name'].label = 'Фамилия'
        self.fields['email'].label = 'Email'
        
        # Применяем стили Duolingo
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control-duolingo'})
