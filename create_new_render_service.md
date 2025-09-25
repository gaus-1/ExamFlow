# Создание нового сервиса на Render

## Шаги для создания нового сервиса:

1. **Зайдите в Render Dashboard**
   - https://dashboard.render.com
   - Нажмите "New +" → "Web Service"

2. **Подключите репозиторий**
   - Repository: `gaus-1/ExamFlow`
   - Branch: `main`
   - Root Directory: оставить пустым

3. **Настройки сборки**
   - Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - Start Command: `gunicorn examflow_project.wsgi:application`

4. **Переменные окружения**
   - `DJANGO_SETTINGS_MODULE=examflow_project.settings`
   - `DEBUG=False`
   - `ALLOWED_HOSTS=examflow-new.onrender.com`

5. **План**
   - Выберите Free (для начала)
   - Или сразу Starter ($7/месяц)

6. **Создать сервис**
   - Нажмите "Create Web Service"
   - Дождитесь первого деплоя (5-10 минут)

## Преимущества нового сервиса:
- ✅ Свежие лимиты pipeline
- ✅ Чистая история деплоев
- ✅ Возможность настроить Auto-Deploy правильно

## После создания:
- Обновите домен в настройках
- Настройте переменные окружения
- Проверьте работу сайта
