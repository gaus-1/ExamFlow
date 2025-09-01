# 🚀 Руководство по деплою ExamFlow 2.0 на examflow.ru

## **📋 Что нужно сделать:**

### **1. Настройка Custom Domain в Render**

1. **Зайдите в Render Dashboard:**
   - Перейдите на https://dashboard.render.com
   - Выберите ваш ExamFlow 2.0 web service

2. **Настройте Custom Domain:**
   - В разделе "Settings" найдите "Custom Domains"
   - Нажмите "Add Custom Domain"
   - Введите: `examflow.ru`
   - Нажмите "Add"

3. **Настройте DNS записи:**
   - В вашем DNS провайдере (где зарегистрирован домен) добавьте CNAME запись:
   ```
   Type: CNAME
   Name: @ (или examflow)
   Value: your-render-service.onrender.com
   TTL: 3600
   ```

### **2. Настройка GitHub Secrets**

В настройках GitHub репозитория (Settings → Secrets and variables → Actions) добавьте:

```
RENDER_TOKEN=your_render_api_token
RENDER_SERVICE_ID=your_service_id
```

### **3. Переменные окружения в Render**

В настройках Render web service добавьте:

```
WEBSITE_URL=https://examflow.ru
SITE_URL=https://examflow.ru
ALLOWED_HOSTS=examflow.ru,www.examflow.ru
```

### **4. SSL сертификат**

Render автоматически настроит SSL сертификат для examflow.ru

## **🔧 Команды для деплоя:**

```bash
# Закоммитить изменения
git add .
git commit -m "Настройка деплоя на examflow.ru"
git push origin main

# Проверить статус деплоя
curl -I https://examflow.ru/health/
```

## **✅ Проверка работоспособности:**

1. **Сайт:** https://examflow.ru
2. **Health check:** https://examflow.ru/health/
3. **Telegram бот:** @examflow_bot
4. **ИИ ассистент:** https://examflow.ru/ai/chat/

## **🚨 Важные моменты:**

- Убедитесь, что старый сайт на examflow.ru остановлен
- DNS изменения могут занять до 24 часов
- Проверьте SSL сертификат
- Настройте мониторинг и алерты

## **📞 Поддержка:**

При проблемах с деплоем:
1. Проверьте логи в Render Dashboard
2. Убедитесь в правильности DNS настроек
3. Проверьте переменные окружения
