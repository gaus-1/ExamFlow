# Настройка PostgreSQL для ExamFlow

## 1. Установка PostgreSQL

### Windows
```bash
# Скачайте и установите с официального сайта
# https://www.postgresql.org/download/windows/
```

### macOS
```bash
brew install postgresql
brew services start postgresql
```

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

## 2. Создание пользователя и базы данных

### Подключение к PostgreSQL
```bash
sudo -u postgres psql
```

### Создание пользователя
```sql
CREATE USER examflow_user WITH PASSWORD 'examflow_password';
```

### Создание базы данных
```sql
CREATE DATABASE examflow_db OWNER examflow_user;
```

### Предоставление прав
```sql
GRANT ALL PRIVILEGES ON DATABASE examflow_db TO examflow_user;
GRANT ALL ON SCHEMA public TO examflow_user;
```

### Выход из psql
```sql
\q
```

## 3. Настройка аутентификации

### Редактирование pg_hba.conf
```bash
sudo nano /etc/postgresql/*/main/pg_hba.conf
```

### Добавьте строку для локального подключения
```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   examflow_db     examflow_user                           md5
```

### Перезапуск PostgreSQL
```bash
sudo systemctl restart postgresql
```

## 4. Проверка подключения

### Тест подключения
```bash
psql -h localhost -U examflow_user -d examflow_db
```

### Введите пароль когда попросит

## 5. Настройка для продакшена (Render)

### Переменные окружения на Render
```
DATABASE_URL=postgresql://username:password@host:port/database
DB_FORCE_IPV4=1
```

### SSL настройки
```
DB_SSL_REQUIRE=True
```

## 6. Миграции Django

### Создание миграций
```bash
python manage.py makemigrations
```

### Применение миграций
```bash
python manage.py migrate
```

### Создание суперпользователя
```bash
python manage.py createsuperuser
```

## 7. Тестирование подключения

### Проверка статуса
```bash
python manage.py check --database default
```

### Проверка таблиц
```bash
python manage.py dbshell
\dt
\q
```

## 8. Резервное копирование

### Создание бэкапа
```bash
pg_dump -h localhost -U examflow_user examflow_db > backup.sql
```

### Восстановление из бэкапа
```bash
psql -h localhost -U examflow_user examflow_db < backup.sql
```

## 9. Мониторинг

### Проверка активных подключений
```sql
SELECT * FROM pg_stat_activity;
```

### Проверка размера БД
```sql
SELECT pg_size_pretty(pg_database_size('examflow_db'));
```

## 10. Устранение неполадок

### Ошибка подключения
- Проверьте, что PostgreSQL запущен
- Проверьте правильность пароля
- Проверьте настройки pg_hba.conf

### Ошибка прав доступа
- Убедитесь, что пользователь имеет права на базу данных
- Проверьте права на схему public

### Ошибка SSL
- Для локальной разработки отключите SSL
- Для продакшена включите SSL и настройте сертификаты
