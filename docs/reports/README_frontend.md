# ExamFlow Frontend — стандарты 2025

- Инструменты: Node 20+, Vite, TypeScript, ESLint, Prettier, Vitest, Husky, commitlint.
- Запуск:
  - npm i
  - npm run lint / npm run test / npm run dev / npm run build
- Сборка через Vite генерируется в static/dist (интеграция по мере миграции). Текущие Django static продолжают работать.
- Кодстайл: ESLint (security/import/promise/a11y) + Prettier.
- Коммиты: conventional commits (commitlint), pre-commit форматирование (husky + lint-staged).
- A11y: ориентируемся на WCAG 2.2; добавлен skip-link, улучшен фокус.

## Миграция JS на TS/Vite
- Новые модули кладём в static/js как .ts/.tsx и подключаем через Vite при готовности.
- Постепенно переносим legacy-скрипты, сохраняя совместимость.

## Тестирование
- Unit: Vitest (npm run test).
- A11y smoke: axe-core + jsdom (добавить по мере внедрения компонентов).

## Дизайн-токены
- Токены определены в static/css/examflow-2.0.css (CSS Custom Properties). Используем переменные вместо жёстких значений.

## CI
- Node-шаги можно подключить в GitHub Actions (eslint/test) без падения основного пайплайна.
