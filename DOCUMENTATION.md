# WellBeing — Документация проекта для защиты диплома

## 1. Общее описание проекта

**WellBeing** — это веб-приложение для мониторинга и поддержки психологического благополучия сотрудников в организации. Система позволяет работникам проходить психологические тесты, вести журнал настроения, общаться с ИИ-ассистентом на базе GPT, а терапевтам — управлять тестовыми вопросами и отслеживать состояние пациентов.

### Целевая аудитория
- **Работники (workers)** — проходят тесты, ведут журнал настроения, общаются с ИИ-ассистентом
- **Терапевты (therapists)** — управляют вопросами тестов, просматривают результаты
- **Администраторы (admins)** — полный доступ к системе управления

---

## 2. Архитектура проекта

Проект построен по архитектуре **клиент-сервер (Client-Server)** с чётким разделением на фронтенд и бэкенд.

```
december_mental_health/
├── Frontend/                  # Клиентская часть (React + Vite)
│   ├── src/
│   │   ├── components/        # UI-компоненты
│   │   ├── contexts/          # React Context (глобальное состояние)
│   │   ├── pages/             # Страницы (дашборды)
│   │   ├── services/          # API-сервисы (HTTP-клиенты)
│   │   ├── styles/            # CSS-стили
│   │   ├── App.jsx            # Корневой компонент с маршрутизацией
│   │   └── main.jsx           # Точка входа
│   ├── package.json           # Зависимости фронтенда
│   └── vite.config.js         # Конфигурация сборщика
│
├── backend/                   # Серверная часть (FastAPI + SQLAlchemy)
│   ├── src/
│   │   ├── api/
│   │   │   └── gpt_client.py  # Интеграция с OpenAI GPT
│   │   ├── main.py            # Главный файл с API-эндпоинтами
│   │   ├── models.py          # ORM-модели базы данных
│   │   ├── schemas.py         # Pydantic-схемы валидации
│   │   ├── database.py        # Подключение к БД
│   │   └── auth.py            # Аутентификация (JWT)
│   └── requirements.txt       # Зависимости бэкенда
│
└── README.md
```

### Схема взаимодействия

```
┌─────────────────┐         HTTP/REST         ┌──────────────────┐
│                 │ ◄──────────────────────── │                  │
│   Frontend      │        JSON               │   Backend        │
│   (React)       │ ────────────────────────► │   (FastAPI)      │
│   Port: 5173    │                           │   Port: 8000     │
└─────────────────┘                           └──────┬───────────┘
                                                     │
                                              ┌──────▼───────────┐
                                              │   PostgreSQL     │
                                              │   (SQLAlchemy)   │
                                              └──────────────────┘
                                                     │
                                              ┌──────▼───────────┐
                                              │   OpenAI API     │
                                              │   (GPT-4o-mini)  │
                                              └──────────────────┘
```

---

## 3. Технологический стек

### 3.1 Фронтенд

| Технология | Версия | Назначение |
|---|---|---|
| **React** | 18.2.0 | Основная UI-библиотека. Выбрана за компонентный подход, Virtual DOM, огромное сообщество и экосистему |
| **Vite** | 7.x | Сборщик проекта. Выбран вместо Webpack за мгновенный запуск dev-сервера (HMR), быструю сборку через ESBuild, и нативную поддержку ES-модулей |
| **React Router DOM** | 7.x | Клиентская маршрутизация. Используется для ролевого перенаправления (admin → `/admin`, therapist → `/therapist`) |
| **React Bootstrap** | 2.10.x | UI-библиотека компонентов на основе Bootstrap 5. Выбрана для ускорения разработки — предоставляет готовые адаптивные компоненты (модальные окна, формы, навбар, таблицы) |
| **Bootstrap** | 5.3.x | CSS-фреймворк. Грид-система, типографика, утилиты |
| **Recharts** | 3.7.x | Библиотека графиков для React. Используется для визуализации аналитики — линейные графики (динамика результатов) и столбчатые диаграммы (удовлетворённость по дням) |

### 3.2 Бэкенд

| Технология | Назначение |
|---|---|
| **FastAPI** | Асинхронный Python-фреймворк для REST API. Выбран за автоматическую генерацию OpenAPI-документации, поддержку async/await, встроенную валидацию через Pydantic, и высокую производительность |
| **SQLAlchemy** | ORM (Object-Relational Mapping). Используется для описания моделей данных и взаимодействия с PostgreSQL через Python-объекты вместо сырых SQL-запросов |
| **PostgreSQL** | Реляционная СУБД. Выбрана за надёжность, поддержку JSON-полей (для хранения вариантов ответов тестов), и масштабируемость |
| **Pydantic** | Библиотека валидации данных. Все входящие запросы (request body) проходят строгую валидацию через Pydantic-схемы |
| **python-jose** | Библиотека для работы с JWT-токенами. Используется для создания и верификации токенов аутентификации |
| **passlib + bcrypt** | Безопасное хеширование паролей. bcrypt — стандартный алгоритм хеширования, устойчивый к brute-force атакам |
| **OpenAI API** | Интеграция с GPT-4o-mini для ИИ-ассистента и генерации аналитических сводок о состоянии пользователя |
| **Uvicorn** | ASGI-сервер для запуска FastAPI-приложения |
| **python-dotenv** | Загрузка переменных окружения из `.env` файла |

### 3.3 Обоснование выбора стека

**Почему FastAPI, а не Django/Flask?**
- FastAPI быстрее Flask за счёт асинхронности (на базе Starlette)
- Автоматическая документация Swagger UI на `/docs` — удобно для разработки и тестирования
- Нативная интеграция с Pydantic — не нужен отдельный слой валидации
- Django был бы избыточен для API-only сервера (не нужен шаблонизатор, админка)

**Почему React, а не Vue/Angular?**
- Самая большая экосистема и сообщество
- Компонентный подход идеально подходит для данного проекта (каждая секция — отдельный компонент)
- Hooks API (useState, useEffect, useContext) позволяют легко управлять состоянием без Redux

**Почему PostgreSQL, а не MySQL/SQLite?**
- Поддержка JSON-полей — варианты ответов тестов хранятся как JSON-массив
- Надёжность и целостность данных для медицинских/психологических данных
- Масштабируемость для производственного использования

---

## 4. База данных — модели и связи

### 4.1 ER-диаграмма (Entity-Relationship)

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     users        │       │    journals      │       │   test_results   │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │◄──┐   │ id (PK)         │       │ id (PK)         │
│ full_name       │   ├──►│ user_id (FK)     │       │ user_id (FK)    │──►
│ mail (UNIQUE)   │   │   │ wellbeing_score  │       │ total_score     │
│ hashed_password │   │   │ note_text        │       │ created_at      │
│ role (ENUM)     │   │   │ created_at       │       └─────────────────┘
└─────────────────┘   │   └─────────────────┘
                      │
                      │   ┌─────────────────┐       ┌─────────────────┐
                      │   │    ai_logs       │       │   ai_summaries   │
                      │   ├─────────────────┤       ├─────────────────┤
                      ├──►│ id (PK)         │       │ id (PK)         │
                      │   │ user_id (FK)     │       │ user_id (FK)    │──►
                      │   │ request          │       │ summary_text    │
                      │   │ response         │       │ created_at      │
                      │   │ created_at       │       └─────────────────┘
                      │   └─────────────────┘
                      │
                      │   ┌─────────────────┐
                      │   │   questions      │
                      │   ├─────────────────┤
                      │   │ id (PK)         │
                      │   │ text            │
                      │   │ options (JSON)  │  ◄── [{text: "...", points: N}, ...]
                      │   └─────────────────┘
```

### 4.2 Описание моделей (`backend/src/models.py`)

**User** — Пользователь системы
```python
class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True)
    full_name     = Column(String)            # ФИО
    mail          = Column(String, unique=True) # Почта (логин)
    hashed_password = Column(String)          # Хеш пароля (bcrypt)
    role          = Column(Enum(UserRole))     # worker / therapist / admin
```
- Поле `role` определяет доступ к функциональности через `UserRole` — enum с тремя значениями
- Пароль **никогда не хранится в открытом виде** — только bcrypt-хеш

**Journal** — Запись журнала настроения
```python
class Journal(Base):
    __tablename__ = "journals"
    id              = Column(Integer, primary_key=True)
    wellbeing_score = Column(Integer)       # Оценка 0-5
    note_text       = Column(String)        # Текст заметки
    created_at      = Column(DateTime)      # Дата создания
    user_id         = Column(Integer, FK)   # Связь с пользователем
```

**Question** — Вопрос теста
```python
class Question(Base):
    __tablename__ = "questions"
    id      = Column(Integer, primary_key=True)
    text    = Column(String)         # Текст вопроса
    options = Column(JSON)           # Варианты ответов в формате JSON
```
- Поле `options` использует тип `JSON` в PostgreSQL — хранит массив объектов `{text, points}`
- Это позволяет гибко добавлять любое количество вариантов ответа

**TestResult** — Результат прохождения теста
```python
class TestResult(Base):
    __tablename__ = "test_results"
    id          = Column(Integer, primary_key=True)
    total_score = Column(Integer)       # Суммарный балл
    created_at  = Column(DateTime)
    user_id     = Column(Integer, FK)
```

**AILog** — Лог запросов к ИИ-ассистенту
```python
class AILog(Base):
    __tablename__ = "ai_logs"
    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, FK)
    request    = Column(String)    # Запрос пользователя
    response   = Column(String)    # Ответ GPT
    created_at = Column(DateTime)
```

**AISummary** — Автоматическая сводка состояния пользователя от ИИ
```python
class AISummary(Base):
    __tablename__ = "ai_summaries"
    id           = Column(Integer, primary_key=True)
    user_id      = Column(Integer, FK)
    summary_text = Column(String)    # Текст сводки
    created_at   = Column(DateTime)
```

---

## 5. Бэкенд — API-эндпоинты и логика

### 5.1 Подключение к базе данных (`backend/src/database.py`)

```python
engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

**Зачем используется паттерн `get_db()`:**
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
Это **генераторная зависимость (dependency)** FastAPI. При каждом HTTP-запросе:
1. Создаётся новая сессия базы данных
2. Передаётся в обработчик эндпоинта через `Depends(database.get_db)`
3. После завершения запроса сессия гарантированно закрывается (`finally`)

Это предотвращает утечки подключений к БД.

### 5.2 Аутентификация и авторизация (`backend/src/auth.py`)

Используется стандарт **OAuth2 с Bearer JWT-токенами**.

**Процесс аутентификации:**
1. Пользователь отправляет email + пароль на `POST /token`
2. Сервер проверяет пароль через `bcrypt.verify()`
3. Генерируется JWT-токен с `sub` (email) и `exp` (время истечения)
4. Токен возвращается клиенту и сохраняется в `localStorage`
5. При каждом запросе клиент отправляет токен в заголовке `Authorization: Bearer <token>`
6. Сервер декодирует токен через `jose.jwt.decode()` и находит пользователя в БД

```python
# Хеширование пароля
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Создание JWT
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

**Почему JWT, а не сессии?**
- JWT не требует хранения сессий на сервере (stateless)
- Масштабируется горизонтально — любой сервер может проверить токен
- Идеально для SPA-приложения (React), где фронтенд и бэкенд — отдельные сервисы

### 5.3 API-эндпоинты (`backend/src/main.py`)

#### Группа AUTH — Аутентификация

| Метод | Путь | Описание | Доступ |
|---|---|---|---|
| `POST` | `/token` | Логин (получение JWT-токена) | Все |
| `POST` | `/register` | Регистрация нового пользователя | Все |
| `GET` | `/auth/me` | Получить информацию о текущем пользователе | Авторизованные |

#### Группа JOURNAL — Журнал настроения

| Метод | Путь | Описание | Доступ |
|---|---|---|---|
| `POST` | `/journal` | Создать запись настроения (score 0-5 + текст) | Авторизованные |
| `GET` | `/journal` | Получить последние 5 записей | Авторизованные |
| `DELETE` | `/journal/{id}` | Удалить запись (только свою) | Авторизованные |

**Важная деталь:** при создании записи журнала запускается **фоновая задача** для генерации AI-сводки:
```python
background_tasks.add_task(gpt_client.generate_user_summary, user.id, db)
```
Это значит, что пользователь не ждёт ответа от GPT — сводка генерируется асинхронно.

#### Группа TESTING — Психологическое тестирование

| Метод | Путь | Описание | Доступ |
|---|---|---|---|
| `POST` | `/test/add-question` | Добавить вопрос | Только терапевты |
| `GET` | `/test/questions` | Получить все вопросы | Авторизованные |
| `DELETE` | `/test/question/{id}` | Удалить вопрос | Только терапевты |
| `POST` | `/test/submit` | Отправить ответы теста | Только workers |
| `GET` | `/test/results` | Получить свои результаты | Только workers |

**Логика подсчёта результатов теста:**
```python
for question_id, option_index in data.answers.items():
    question = db.query(models.Question).filter(...).first()
    total_score += question.options[option_index]["points"]
```
Каждый вариант ответа имеет определённое количество баллов. При отправке теста сервер суммирует баллы выбранных ответов.

#### Группа AI — Искусственный интеллект

| Метод | Путь | Описание | Доступ |
|---|---|---|---|
| `POST` | `/ai/ask` | Отправить вопрос ИИ-ассистенту | Авторизованные |

### 5.4 Интеграция с OpenAI GPT (`backend/src/api/gpt_client.py`)

В проекте реализованы **два AI-сценария:**

#### Сценарий 1: Автоматическая генерация сводки (`generate_user_summary`)

Запускается **фоновой задачей** после:
- Создания записи в журнале настроения
- Отправки результатов теста

**Алгоритм:**
1. Из БД загружаются последние 10 записей журнала и 5 результатов тестов
2. Формируется промпт с инструкцией для GPT: проанализировать состояние, выделить тенденции, дать совет
3. Отправляется запрос к `gpt-4o-mini` с `max_tokens=500`
4. Результат сохраняется в таблицу `ai_summaries`

```python
prompt = f"""
Ты психологический ассистент.
Сделай краткую выжимку состояния пользователя.
Тесты: {test_text}
Заметки: {journal_text}
Сформулируй: общее состояние, тенденции, краткий совет
"""
```

#### Сценарий 2: Чат с AI-ассистентом (`ask_ai_assistant`)

Пользователь задаёт вопросы в чате, GPT отвечает с учётом контекста.

**Алгоритм:**
1. Загружается последняя AI-сводка пользователя (из `ai_summaries`)
2. Формируется системный промпт с ролью «психологический ассистент» + контекст о пользователе
3. Сообщение пользователя отправляется как user-message
4. Ответ GPT логируется в таблицу `ai_logs`

**Почему GPT-4o-mini, а не GPT-4o?**
- Дешевле (в ~10 раз) при достаточном качестве для психологических рекомендаций
- Быстрее отвечает — важно для UX чата
- Для данного уровня задачи полная модель GPT-4o избыточна

### 5.5 Валидация данных (`backend/src/schemas.py`)

Все входящие данные проходят через **Pydantic-схемы**:

```python
class QuestionCreate(BaseModel):     # Создание вопроса
    text: str
    options: List[OptionCreate]      # Массив вариантов {text, points}

class TestSubmit(BaseModel):         # Отправка теста
    answers: dict[int, int]          # {question_id: option_index}

class JournalCreate(BaseModel):      # Создание записи журнала
    score: int                       # 0-5
    note: str = None                 # Текст (опционально)

class AIAsk(BaseModel):              # Запрос к ИИ
    prompt: str
```

**Зачем Pydantic:**
- Автоматическая валидация типов (число ≠ строка)
- Автоматическая сериализация JSON ↔ Python
- Генерация OpenAPI-схемы для документации

### 5.6 CORS-настройки

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", os.getenv("FRONTEND_URL", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
Разрешает фронтенду (порт 5173) делать запросы к бэкенду (порт 8000). Без CORS браузер блокировал бы все кросс-доменные запросы.

---

## 6. Фронтенд — компонентная архитектура

### 6.1 Точка входа и маршрутизация

**`main.jsx`** — точка входа приложения:
```jsx
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

**`App.jsx`** — корневой компонент с ролевой маршрутизацией:
```
App
├── Router (BrowserRouter)
│   └── AuthProvider (контекст авторизации)
│       └── AppContent (условный рендеринг по роли)
│           ├── [role=admin]     → AdminDashboard
│           ├── [role=therapist] → TherapistDashboard
│           └── [role=worker / гость] → Главная страница
│               ├── Navbar
│               ├── AuthModal
│               ├── Hero
│               ├── MaterialsSection
│               ├── TestSection + TestModal
│               ├── TestResultsHistory
│               ├── AIAssistantSection + AIChatModal
│               ├── MoodJournal
│               ├── BurnoutScale
│               ├── AnalyticsSection
│               └── Footer
```

**Ролевая маршрутизация** — ключевой архитектурный выбор. Вместо отдельных маршрутов для каждой страницы, используется условный рендеринг на основе роли пользователя:
- Админ автоматически перенаправляется на `/admin`
- Терапевт — на `/therapist`
- Работник видит главную страницу с полным функционалом

### 6.2 Управление состоянием — AuthContext

Файл: `Frontend/src/contexts/AuthContext.jsx`

Используется **React Context API** для глобального управления аутентификацией.

```jsx
const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // При загрузке — проверяем localStorage
  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    const token = localStorage.getItem('token');
    if (savedUser && token) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const login = (userData, token) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
    localStorage.setItem('token', token);
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
    localStorage.removeItem('token');
  };
};
```

**Почему Context API, а не Redux/MobX?**
- Состояние простое — только `user` и `loading`
- Context API встроен в React — не нужны дополнительные зависимости
- Для данного масштаба Redux был бы over-engineering

**Где используется:**
- `Navbar` — показывает кнопки Login/Logout
- `App` — определяет роль и рендерит нужный контент
- `MoodJournal` — проверяет авторизацию перед записью
- `TestSection` — передаёт `userId` в модальное окно

### 6.3 HTTP-клиент (`Frontend/src/services/api.js`)

Реализован класс `ApiService` — обёртка над `fetch()` с:

1. **Автоматической подстановкой JWT-токена** в заголовок `Authorization`
2. **Retry-логикой** (до 3 попыток) с экспоненциальной задержкой (2s, 4s, 8s)
3. **Таймаутом** в 10 секунд через `AbortController`

```javascript
class ApiService {
  async request(endpoint, options = {}) {
    const maxRetries = 3;
    const timeout = 10000;
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      const controller = new AbortController();
      timeoutId = setTimeout(() => controller.abort(), timeout);
      const response = await fetch(url, { ...options, signal: controller.signal });
      // ... обработка ответа ...
      // При ошибке — экспоненциальная задержка
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
    }
  }
}
```

**Зачем retry с экспоненциальной задержкой:**
- Защита от кратковременных сбоев сети
- Экспоненциальная задержка не перегружает сервер повторами
- Стандартный паттерн для надёжных клиентских приложений

### 6.4 Описание ключевых компонентов

#### `Navbar.jsx` — Навигационная панель
- Sticky-навигация (закреплена при прокрутке)
- Плавная прокрутка к секциям через `scrollIntoView({ behavior: "smooth" })`
- Адаптивный бургер-меню для мобильных устройств (Bootstrap Collapse)
- Условный рендеринг кнопок: Login/SignUp для гостей, Logout для авторизованных

#### `AuthModal.jsx` — Модальное окно аутентификации
- **Два таба:** Вход и Регистрация
- Клиентская валидация: ФИО, совпадение паролей, минимум 8 символов
- Выбор роли при регистрации: Рабочий / Терапевт
- После успешной регистрации автоматически выполняется вход
- Используются компоненты React Bootstrap: `Modal`, `Tabs`, `Form`, `Alert`

#### `Hero.jsx` — Главный баннер
- Приветственная секция с описанием приложения
- CSS-анимация появления (fade-in)

#### `MaterialsSection.jsx` — Полезные материалы
- Карточки с психологическими ресурсами (Burnout, Mindfulness, Sleep, Stress)
- Адаптивная сетка: 4 колонки на десктопе, 2 на планшете, 1 на мобильном

#### `TestSection.jsx` + `TestModal.jsx` — Тестирование
- Кнопка «Start the Test» открывает модальное окно
- Вопросы загружаются с бэкенда (`GET /test/questions`)
- Пошаговая навигация между вопросами (Назад/Далее)
- Прогресс-бар показывает текущий прогресс
- Radio-кнопки для выбора варианта ответа
- При завершении — отправка на `POST /test/submit` и показ результата

#### `TestResultsHistory.jsx` — История результатов
- Загружает результаты с `GET /test/results`
- Карточки с баллами, датой и цветовым Badge (Отлично/Хорошо/Средне/Требует внимания)
- Визуальный прогресс-бар для каждого результата
- Модальное окно с подробностями

#### `AIAssistantSection.jsx` + `AIChatModal.jsx` — ИИ-ассистент
- Секция-презентация AI-ассистента с кнопкой «Chat Now»
- **AIChatModal** — полноценный чат:
  - Левая панель — автоматические рекомендации на основе данных пользователя
  - Правая панель — чат-интерфейс
  - Сообщения пользователя отправляются на `POST /ai/ask`
  - Автоскролл к последнему сообщению
  - Состояние загрузки (спиннер) при ожидании ответа

#### `MoodJournal.jsx` — Журнал настроения
- Выбор эмоции через emoji-кнопки (6 уровней: 😢→🤩, оценки 0-5)
- Текстовое поле для заметки
- Отправка на `POST /journal` с score и note
- Статистика: средний уровень настроения
- История записей с возможностью удаления

#### `BurnoutScale.jsx` — Шкала выгорания
- Визуальная шкала риска выгорания (прогресс-бар)
- Текущая реализация использует статическое значение (35%)

#### `AnalyticsSection.jsx` — Аналитика
- **Линейный график** (LineChart) — динамика результатов тестов по неделям
- **Столбчатая диаграмма** (BarChart) — удовлетворённость по дням недели
- Библиотека Recharts с адаптивными контейнерами

### 6.5 Страницы дашбордов

#### `AdminDashboard.jsx` — Панель администратора
- Отдельный навбар с именем пользователя
- 4 секции-карточки: Пользователи, Тесты, Отчёты, Настройки
- Каркас для расширения функциональности

#### `TherapistDashboard.jsx` — Панель терапевта
- Таблица со всеми вопросами тестов
- Кнопка «Добавить вопрос» → модальное окно с формой:
  - Текст вопроса
  - Динамическое добавление/удаление вариантов ответа
  - Указание баллов для каждого варианта
- Удаление вопросов с подтверждением через `window.confirm()`

---

## 7. Безопасность

### 7.1 Аутентификация
- Пароли хешируются через **bcrypt** — необратимый алгоритм, устойчивый к радужным таблицам
- JWT-токены с временем жизни (по умолчанию 1440 минут = 24 часа)
- Секретный ключ хранится в переменных окружения (`.env`)

### 7.2 Авторизация (ролевой доступ)
- Каждый эндпоинт проверяет роль через `user.role`:
  - Добавление/удаление вопросов — только `therapist`
  - Прохождение тестов и просмотр результатов — только `worker`
  - Удаление записей журнала — только владелец записи (`journal.user_id != user.id`)

### 7.3 CORS
- Разрешены только домены фронтенда (`localhost:5173` + переменная `FRONTEND_URL`)
- Передача credentials (куки, токены) разрешена

### 7.4 Валидация данных
- Pydantic-схемы на бэкенде валидируют все входящие данные
- Клиентская валидация на фронтенде (проверка паролей, обязательных полей)
- Проверка score в журнале: `0 <= data.score <= 5`
- Проверка индекса варианта ответа: `0 <= option_index < len(options)`

---

## 8. Паттерны проектирования

### 8.1 Component-Based Architecture (Фронтенд)
Каждый UI-элемент — отдельный компонент с собственным состоянием и логикой. Это обеспечивает:
- Переиспользуемость
- Изолированное тестирование
- Параллельную разработку

### 8.2 Service Layer Pattern (Фронтенд)
HTTP-запросы вынесены в отдельные сервисы (`api.js`, `authService.js`, `testService.js`). Компоненты не знают деталей API — они вызывают методы сервисов.

### 8.3 Dependency Injection (Бэкенд)
FastAPI использует систему `Depends()` для инъекции зависимостей:
```python
def login(form_data = Depends(), db: Session = Depends(database.get_db)):
```
Это позволяет легко подменять зависимости для тестирования.

### 8.4 Background Tasks (Бэкенд)
Генерация AI-сводок выполняется через `BackgroundTasks` FastAPI — пользователь не ждёт ответа GPT при записи в журнал.

### 8.5 Repository Pattern (частично)
SQLAlchemy ORM-модели инкапсулируют доступ к БД. Вся работа с данными — через объекты Python, а не сырой SQL.

---

## 9. Конфигурация и деплой

### 9.1 Переменные окружения

**Backend (`.env`):**
```
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
OPENAI_API_KEY=sk-...
FRONTEND_URL=https://your-frontend.com
```

**Frontend (`.env`):**
```
VITE_API_URL=http://localhost:8000
```

### 9.2 Запуск проекта

**Бэкенд:**
```bash
cd backend
pip install -r requirements.txt
cd src
uvicorn main:app --reload --port 8000
```

**Фронтенд:**
```bash
cd Frontend
npm install
npm run dev    # Запуск dev-сервера на порту 5173
npm run build  # Продакшен-сборка
```

### 9.3 Деплой
- Бэкенд подготовлен для деплоя на **Vercel** (наличие `vercel.json`)
- Фронтенд собирается Vite в статические файлы и может быть размещён на любом хостинге (Vercel, Netlify, и т.д.)

---

## 10. Резюме — ключевые технические решения

| Решение | Обоснование |
|---|---|
| React + Vite | Быстрая разработка, мгновенный HMR, современный стек |
| FastAPI + SQLAlchemy | Высокая производительность, автодокументация, ORM |
| JWT-аутентификация | Stateless, масштабируемость, стандарт для SPA |
| PostgreSQL + JSON поля | Надёжность + гибкость хранения вариантов ответов |
| OpenAI GPT-4o-mini | Баланс качества и стоимости для психологического ассистента |
| React Context API | Простое глобальное состояние без лишних зависимостей |
| Background Tasks | Асинхронная генерация AI-сводок не блокирует UX |
| Pydantic-схемы | Строгая валидация на границе API |
| Retry + Exponential Backoff | Надёжность клиентских запросов |
| Ролевой доступ | Разделение функциональности по типам пользователей |