## Корпоративные стандарты кода (2025)

Обязательны ко всем проектам. Проверяются pre-commit и CI.

### I. Python (PEP8 + Modern)
- Отступы 4 пробела, длина строки ≤ 88.
- Именование: snake_case (функции/переменные), CamelCase (классы), UPPER_SNAKE_CASE (константы).
- Импорты: stdlib → third-party → local; абсолютные пути; isort/ruff.
- Аннотации типов обязательны в публичном API и сервисах.
- Исключения: только конкретные типы; без bare `except`; логирование с контекстом.
- Контекстные менеджеры для ресурсов; докстринги Google/PEP257.

### II. Django
- Настройки по окружениям; секреты в env; DEBUG=False в prod.
- Миграции атомарны; ORM без N+1; `select_related/prefetch_related`.
- Валидация входа: формы/сериализаторы; защита XSS по умолчанию.

### III. HTML (Semantics + A11y)
- Семантика: header/nav/main/section/article/footer.
- WCAG 2.1 AA: alt, lang, aria/role; валидная иерархия заголовков.
- SEO: уникальные `title` и `meta description`.

### IV. CSS (BEM + Vars + Responsive)
- BEM (`block__element--modifier`), запрет `!important`.
- CSS variables в `:root`; `rem/em`; mobile-first медиазапросы.

### V. JavaScript (ES6+ Security)
- ESM модули, стрелочные функции, деструктуризация.
- Безопасность: `textContent`, запрет `eval/new Function`, CSP.
- ESLint (Airbnb + security), тесты для критичных модулей.

### VI. Безопасность
- HTTPS, HSTS, CSRF, куки HttpOnly/SameSite=Strict.
- Санитизация ввода/вывода; защита от XSS/SQLi/SSRF/XXE.
- Секреты только из переменных окружения; обновления зависят от Dependabot.

### VII. Git и CI/CD
- Conventional Commits, обязательный код-ревью.
- Pre-commit: black, isort, ruff, eslint, stylelint, prettier.
- CI блокирует мёрджи при ошибках линтеров/тестов/безопасности.

### VIII. Документация
- README актуален; ADR в `docs/adr/` для ключевых решений.

### IX. Запрещено
- Глобальные переменные в JS; смешение кейсов; отсутствие type hints; div-soup; хардкод секретов; bare except; заглушки.
