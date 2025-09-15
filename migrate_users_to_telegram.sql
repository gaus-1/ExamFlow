-- Скрипт миграции данных пользователей с user_id на telegram_id
-- ВАЖНО: Выполнять только после создания всех миграций!

-- 1. Обновляем UnifiedProfile для связи с telegram_id вместо user_id
UPDATE core_unifiedprofile 
SET telegram_id = (
    SELECT telegram_id 
    FROM telegram_auth_telegramuser 
    WHERE telegram_auth_telegramuser.id = core_unifiedprofile.user_id
)
WHERE user_id IS NOT NULL;

-- 2. Обновляем ChatSession для связи с telegram_id
UPDATE core_chatsession 
SET telegram_id = (
    SELECT telegram_id 
    FROM telegram_auth_telegramuser 
    WHERE telegram_auth_telegramuser.id = core_chatsession.user_id
)
WHERE user_id IS NOT NULL;

-- 3. Обновляем UserProgress для связи с telegram_id
UPDATE core_userprogress 
SET user_id = (
    SELECT id 
    FROM telegram_auth_telegramuser 
    WHERE telegram_auth_telegramuser.telegram_id = core_userprogress.user_id
)
WHERE user_id IS NOT NULL;

-- 4. Обновляем UserProfile для связи с telegram_id
UPDATE core_userprofile 
SET user_id = (
    SELECT id 
    FROM telegram_auth_telegramuser 
    WHERE telegram_auth_telegramuser.telegram_id = core_userprofile.user_id
)
WHERE user_id IS NOT NULL;

-- 5. Обновляем UserProgress в learning
UPDATE learning_userprogress 
SET user_id = (
    SELECT id 
    FROM telegram_auth_telegramuser 
    WHERE telegram_auth_telegramuser.telegram_id = learning_userprogress.user_id
)
WHERE user_id IS NOT NULL;

-- 6. Обновляем UserRating
UPDATE learning_userrating 
SET user_id = (
    SELECT id 
    FROM telegram_auth_telegramuser 
    WHERE telegram_auth_telegramuser.telegram_id = learning_userrating.user_id
)
WHERE user_id IS NOT NULL;

-- 7. Обновляем UserAchievement
UPDATE learning_userachievement 
SET user_id = (
    SELECT id 
    FROM telegram_auth_telegramuser 
    WHERE telegram_auth_telegramuser.telegram_id = learning_userachievement.user_id
)
WHERE user_id IS NOT NULL;

-- 8. Обновляем UserThemePreference
UPDATE themes_userthemepreference 
SET user_id = (
    SELECT id 
    FROM telegram_auth_telegramuser 
    WHERE telegram_auth_telegramuser.telegram_id = themes_userthemepreference.user_id
)
WHERE user_id IS NOT NULL;

-- 9. Обновляем ThemeCustomization
UPDATE themes_themecustomization 
SET user_id = (
    SELECT id 
    FROM telegram_auth_telegramuser 
    WHERE telegram_auth_telegramuser.telegram_id = themes_themecustomization.user_id
)
WHERE user_id IS NOT NULL;

-- 10. Обновляем ThemeUsage
UPDATE themes_themeusage 
SET user_id = (
    SELECT id 
    FROM telegram_auth_telegramuser 
    WHERE telegram_auth_telegramuser.telegram_id = themes_themeusage.user_id
)
WHERE user_id IS NOT NULL;

-- 11. Обновляем AiRequest
UPDATE ai_airequest 
SET user_id = (
    SELECT id 
    FROM telegram_auth_telegramuser 
    WHERE telegram_auth_telegramuser.telegram_id = ai_airequest.user_id
)
WHERE user_id IS NOT NULL;

-- 12. Обновляем AiLimit
UPDATE ai_ailimit 
SET user_id = (
    SELECT id 
    FROM telegram_auth_telegramuser 
    WHERE telegram_auth_telegramuser.telegram_id = ai_ailimit.user_id
)
WHERE user_id IS NOT NULL;

-- Проверяем результаты
SELECT 'UnifiedProfile' as table_name, COUNT(*) as records FROM core_unifiedprofile WHERE telegram_id IS NOT NULL
UNION ALL
SELECT 'ChatSession', COUNT(*) FROM core_chatsession WHERE telegram_id IS NOT NULL
UNION ALL
SELECT 'UserProgress (core)', COUNT(*) FROM core_userprogress WHERE user_id IS NOT NULL
UNION ALL
SELECT 'UserProfile', COUNT(*) FROM core_userprofile WHERE user_id IS NOT NULL
UNION ALL
SELECT 'UserProgress (learning)', COUNT(*) FROM learning_userprogress WHERE user_id IS NOT NULL
UNION ALL
SELECT 'UserRating', COUNT(*) FROM learning_userrating WHERE user_id IS NOT NULL
UNION ALL
SELECT 'UserAchievement', COUNT(*) FROM learning_userachievement WHERE user_id IS NOT NULL
UNION ALL
SELECT 'UserThemePreference', COUNT(*) FROM themes_userthemepreference WHERE user_id IS NOT NULL
UNION ALL
SELECT 'ThemeCustomization', COUNT(*) FROM themes_themecustomization WHERE user_id IS NOT NULL
UNION ALL
SELECT 'ThemeUsage', COUNT(*) FROM themes_themeusage WHERE user_id IS NOT NULL
UNION ALL
SELECT 'AiRequest', COUNT(*) FROM ai_airequest WHERE user_id IS NOT NULL
UNION ALL
SELECT 'AiLimit', COUNT(*) FROM ai_ailimit WHERE user_id IS NOT NULL;
