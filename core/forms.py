"""
Формы для аутентификации и регистрации пользователей
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile


class TechRegisterForm(UserCreationForm):
    """Форма регистрации с технологичным дизайном"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    phone = forms.CharField(max_length=20, required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем технологичные CSS классы
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control-tech',
                'placeholder': self._get_placeholder(field_name)
            })
    
    def _get_placeholder(self, field_name):
        """Возвращает placeholder для поля"""
        placeholders = {
            'username': 'Имя пользователя',
            'email': 'Email адрес',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'password1': 'Пароль',
            'password2': 'Подтверждение пароля',
            'phone': 'Телефон (необязательно)'
        }
        return placeholders.get(field_name, '')
    
    def save(self, commit=True):
        """Сохраняет пользователя и создает профиль"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Создаем профиль пользователя
            UserProfile.objects.create(
                user=user,
                phone=self.cleaned_data.get('phone', '')
            )
        return user


class TechLoginForm(AuthenticationForm):
    """Форма входа с технологичным дизайном"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control-tech',
            'placeholder': 'Имя пользователя или Email'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control-tech',
            'placeholder': 'Пароль'
        })


class ProfileUpdateForm(forms.ModelForm):
    """Форма обновления профиля"""
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = UserProfile
        fields = ['phone', 'telegram_id']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
        
        # Добавляем технологичные CSS классы
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control-tech',
                'placeholder': self._get_placeholder(field_name)
            })
    
    def _get_placeholder(self, field_name):
        """Возвращает placeholder для поля"""
        placeholders = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email адрес',
            'phone': 'Телефон',
            'telegram_id': 'Telegram ID (автоматически)'
        }
        return placeholders.get(field_name, '')
    
    def save(self, commit=True):
        """Сохраняет профиль и обновляет данные пользователя"""
        profile = super().save(commit=False)
        
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save()
        
        if commit:
            profile.save()
        return profile
