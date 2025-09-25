# Пошаговая инструкция создания нового Render сервиса

## 🚀 Шаг 1: Создание нового сервиса

1. **Откройте Render Dashboard**
   - https://dashboard.render.com
   - Нажмите **"New +"** → **"Web Service"**

2. **Подключите репозиторий**
   - Repository: `https://github.com/gaus-1/ExamFlow`
   - Branch: `main`
   - Root Directory: оставить пустым

## ⚙️ Шаг 2: Настройка сборки

3. **Build & Deploy настройки**
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - **Start Command**: `gunicorn examflow_project.wsgi:application --bind 0.0.0.0:$PORT`

4. **План**
   - Выберите **Free** (для начала)
   - Или **Starter** ($7/месяц) - рекомендуется

## 🔧 Шаг 3: Переменные окружения

5. **Environment Variables**
   - Нажмите **"Add Environment Variable"**
   - Добавьте каждую переменную из файла `render_env_variables.txt`

   **Обязательные переменные:**
   ```
   SECRET_KEY=0#$7i40s#%1i&-8$q14f=195_c-4-inwy*-73*xf=t!v_7v=(t
   DEBUG=False
   DATABASE_URL=postgresql://examflow_db_user:b6ltQLqpMIwfUoX7wBwvgTcpOunPAhdl@dpg-d2dn09ali9vc73b2lg7g-a.oregon-postgres.render.com/examflow_db?sslmode=require
   REDIS_URL=rediss://red-d2qldkje5dus73c73tr0:zccbozd9aZ5sbiSSZ8xZaJpW9qM3BnOz@oregon-keyvalue.render.com:6379
   ALLOWED_HOSTS=examflow.ru,www.examflow.ru,examflow-new.onrender.com
   TELEGRAM_BOT_TOKEN=8314335876:AAGzzX6US0xx5PGJ5pVnNJFh7KYeqdSOwLg
   GEMINI_API_KEY=AIzaSyCvi8Mm5paqqV-bakd2N897MgUEvJyWw44
   ```

## 🌐 Шаг 4: Создание и тестирование

6. **Создать сервис**
   - Нажмите **"Create Web Service"**
   - Дождитесь первого деплоя (5-10 минут)

7. **Проверить работу**
   - Откройте URL нового сервиса
   - Проверьте что сайт загружается
   - Проверьте подключение к базе данных

## 🔗 Шаг 5: Настройка домена

8. **Custom Domain** (опционально)
   - В настройках сервиса найдите **"Custom Domains"**
   - Добавьте `examflow.ru`
   - Обновите DNS записи у провайдера домена

## ✅ Шаг 6: Финальная проверка

9. **Тестирование функций**
   - ✅ Главная страница загружается
   - ✅ База данных работает
   - ✅ Telegram Bot отвечает
   - ✅ AI функции работают
   - ✅ Пользователи могут регистрироваться

## 🎯 Преимущества нового сервиса:

- ✅ **Свежие лимиты pipeline** - деплои не блокируются
- ✅ **Та же база данных** - все данные сохраняются
- ✅ **Те же API ключи** - все функции работают
- ✅ **Чистая история** - нет заблокированных деплоев
- ✅ **Правильные настройки** - можно настроить Auto-Deploy правильно

## ⏱️ Время создания: 15-30 минут

## 💰 Стоимость: Free или $7/месяц (Starter)
