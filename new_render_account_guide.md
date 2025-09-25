# Создание нового Render аккаунта

## 🆕 Шаг 1: Создание нового аккаунта

1. **Откройте новую вкладку в браузере**
2. **Перейдите на** https://render.com
3. **Нажмите "Get Started for Free"**
4. **Войдите через GitHub** (используйте тот же GitHub аккаунт)

## 🔗 Шаг 2: Подключение репозитория

1. **Нажмите "New +" → "Web Service"**
2. **Подключите репозиторий**: `gaus-1/ExamFlow`
3. **Branch**: `main`

## ⚙️ Шаг 3: Настройка сервиса

**Name**: `examflow-new` (или любое доступное)

**Build Command**:
```bash
pip install -r requirements-render.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

**Start Command**:
```bash
gunicorn examflow_project.wsgi:application --bind 0.0.0.0:$PORT
```

## 🔧 Шаг 4: Переменные окружения

Скопируйте из файла `render_env_fixed.txt`:

```
SECRET_KEY=0#$7i40s#%1i&-8$q14f=195_c-4-inwy*-73*xf=t!v_7v=(t
DEBUG=False
DJANGO_SETTINGS_MODULE=examflow_project.settings_render
DATABASE_URL=postgresql://examflow_db_user:b6ltQLqpMIwfUoX7wBwvgTcpOunPAhdl@dpg-d2dn09ali9vc73b2lg7g-a.oregon-postgres.render.com/examflow_db?sslmode=require
ALLOWED_HOSTS=examflow.ru,www.examflow.ru,examflow-new.onrender.com
TELEGRAM_BOT_TOKEN=8314335876:AAGzzX6US0xx5PGJ5pVnNJFh7KYeqdSOwLg
GEMINI_API_KEY=AIzaSyCvi8Mm5paqqV-bakd2N897MgUEvJyWw44
ADMIN_CHAT_ID=963126718
ADMIN_USERNAMES=SavinVE
RENDER=true
PYTHON_VERSION=3.11.0
```

## ✅ Шаг 5: Создание сервиса

1. **Нажмите "Create Web Service"**
2. **Дождитесь деплоя** (5-10 минут)
3. **Проверьте работу** сайта

## 🌐 Шаг 6: Настройка домена

1. **В настройках сервиса** найдите "Custom Domains"
2. **Добавьте домен**: `examflow.ru`
3. **Обновите DNS** у провайдера домена

## 💰 Преимущества нового аккаунта:

- ✅ **Свежие лимиты** - 750 минут pipeline
- ✅ **Рабочие деплои** - нет блокировок
- ✅ **Та же база данных** - все данные сохранятся
- ✅ **Те же API ключи** - все функции работают
- ✅ **Бесплатно** - можно использовать Free план

## ⏱️ Время создания: 15-30 минут
