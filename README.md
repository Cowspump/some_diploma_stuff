# WellBeing — Платформа психологической поддержки сотрудников

Веб-приложение для мониторинга и поддержки психологического благополучия сотрудников в организации. Система объединяет психологическое тестирование, дневник настроения и ИИ-ассистента на базе GPT в единую платформу с ролевым доступом.

## Функционал

### Для сотрудников (worker)
- **Психологическое тестирование** — прохождение тестов, созданных терапевтом, с автоматическим подсчётом баллов и сохранением истории результатов
- **Дневник настроения** — ежедневные записи с оценкой состояния (0–5) и текстовыми заметками, просмотр истории и статистики
- **ИИ-ассистент** — чат с GPT-4o-mini, который учитывает контекст пользователя (результаты тестов, записи журнала) и даёт персонализированные рекомендации
- **Аналитика** — графики динамики результатов тестов и настроения (линейные и столбчатые диаграммы)
- **Шкала выгорания** — визуальный индикатор уровня профессионального выгорания
- **Полезные материалы** — подборка ресурсов по темам: выгорание, осознанность, сон, стресс

### Для терапевтов (therapist)
- **Управление тестами** — создание, редактирование и удаление вопросов с вариантами ответов и балльной системой
- **Панель мониторинга** — просмотр данных пациентов и результатов тестирования

### Для администраторов (admin)
- **Панель управления** — доступ к управлению пользователями, тестами, отчётами и настройками системы

### Общее
- **Мультиязычность** — интерфейс на русском, английском и китайском языках
- **Автоматические AI-сводки** — после каждой записи в журнале или прохождения теста GPT генерирует аналитическую сводку состояния пользователя (фоновая задача, не блокирует UX)

---

## Технологический стек

| Слой | Технологии |
|---|---|
| **Frontend** | React 18, Vite, React Router DOM, React Bootstrap, Recharts |
| **Backend** | FastAPI, SQLAlchemy, Pydantic, Uvicorn |
| **База данных** | PostgreSQL |
| **Аутентификация** | JWT (python-jose), bcrypt (passlib) |
| **ИИ** | OpenAI API (GPT-4o-mini) |

---

## Архитектура

```
Frontend (React, порт 5173)
    │
    │  HTTP/REST + JSON
    ▼
Backend (FastAPI, порт 8000)
    │
    ├──► PostgreSQL (SQLAlchemy ORM)
    │
    └──► OpenAI API (GPT-4o-mini)
```

### Структура проекта

```
december_mental_health/
├── Frontend/
│   └── src/
│       ├── components/       # UI-компоненты (Navbar, AuthModal, MoodJournal, TestModal, AIChatModal, ...)
│       ├── contexts/         # React Context (AuthContext, LanguageContext)
│       ├── pages/            # AdminDashboard, TherapistDashboard
│       ├── services/         # HTTP-клиент с retry и таймаутами
│       ├── i18n/             # Переводы (ru, en, zh)
│       ├── styles/           # CSS
│       ├── App.jsx           # Ролевая маршрутизация
│       └── main.jsx          # Точка входа
│
├── backend/
│   ├── src/
│   │   ├── main.py           # API-эндпоинты
│   │   ├── models.py         # ORM-модели (User, Journal, Question, TestResult, AILog, AISummary)
│   │   ├── schemas.py        # Pydantic-схемы валидации
│   │   ├── database.py       # Подключение к PostgreSQL
│   │   ├── auth.py           # JWT-аутентификация
│   │   └── api/
│   │       └── gpt_client.py # Интеграция с OpenAI
│   └── requirements.txt
│
└── README.md
```

---

## Запуск проекта

### Требования

- Python 3.10+
- Node.js 18+
- PostgreSQL

### 1. База данных

Создайте базу данных в PostgreSQL:

```sql
CREATE DATABASE wellbeing;
```

### 2. Backend

```bash
cd backend
python -m venv venv

# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

pip install -r requirements.txt
```

Создайте файл `backend/.env` (пример в `backend/.env_EXAMPLE`):

```env
DATABASE_URL=postgresql://username:password@localhost:5432/wellbeing
SECRET_KEY=ваш-секретный-ключ
OPENAI_API_KEY=sk-ваш-ключ-openai
```

Запуск:

```bash
uvicorn src.main:app --reload
```

Бэкенд будет доступен на `http://localhost:8000`, Swagger-документация — на `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd Frontend
npm install
```

Создайте файл `Frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

Запуск:

```bash
npm run dev
```

Приложение будет доступно на `http://localhost:5173`.

### 4. Первый запуск

1. Зарегистрируйте аккаунт терапевта (роль **therapist**) — создайте вопросы для тестов
2. Зарегистрируйте аккаунт сотрудника (роль **worker**) — проходите тесты, ведите дневник, общайтесь с ИИ

---

## API-эндпоинты

| Метод | Путь | Описание | Доступ |
|---|---|---|---|
| `POST` | `/register` | Регистрация | Все |
| `POST` | `/token` | Авторизация (получение JWT) | Все |
| `GET` | `/auth/me` | Текущий пользователь | Авторизованные |
| `POST` | `/journal` | Создать запись в дневнике | Авторизованные |
| `GET` | `/journal` | Получить записи дневника | Авторизованные |
| `DELETE` | `/journal/{id}` | Удалить запись | Автор записи |
| `POST` | `/test/add-question` | Добавить вопрос | Терапевт |
| `GET` | `/test/questions` | Получить вопросы | Авторизованные |
| `DELETE` | `/test/question/{id}` | Удалить вопрос | Терапевт |
| `POST` | `/test/submit` | Отправить ответы | Worker |
| `GET` | `/test/results` | Результаты тестов | Worker |
| `POST` | `/ai/ask` | Вопрос ИИ-ассистенту | Авторизованные |
