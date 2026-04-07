# WellBeing — Setup Guide (Windows + VS Code)

## Prerequisites

1. **Python 3.12+** — https://www.python.org/downloads/
   - During installation check **"Add Python to PATH"**
2. **Node.js 18+** — https://nodejs.org/
3. **PostgreSQL 15+** — https://www.postgresql.org/download/windows/
   - Remember the password you set for user `postgres`
4. **VS Code** — https://code.visualstudio.com/
5. **Git** — https://git-scm.com/download/win

---

## 1. Clone the repository

```bash
git clone <repository-url>
cd december_mental_health
```

---

## 2. Database setup

Open **pgAdmin** or **psql** terminal and run:

```sql
CREATE DATABASE wellbeing;
```

> **If you had an old version of the project**, the database schema has changed (new tables and columns). The easiest way to fix this:
>
> ```sql
> -- Connect to your database first
> \c wellbeing
> DROP SCHEMA public CASCADE;
> CREATE SCHEMA public;
> ```
>
> This will delete all data and let the app recreate tables from scratch.

---

## 3. Backend setup

Open a terminal in VS Code (`Ctrl+`` `):

```bash
cd backend/src
```

### 3.1 Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3.2 Install dependencies

```bash
pip install -r ../requirements.txt
```

### 3.3 Create `.env` file

Create file `backend/src/.env` with:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/wellbeing
SECRET_KEY=any-random-string-here-123
OPENAI_API_KEY=sk-your-openai-api-key
```

Replace:
- `YOUR_PASSWORD` — your PostgreSQL password
- `sk-your-openai-api-key` — your OpenAI API key (get one at https://platform.openai.com/api-keys)

### 3.4 Run the backend

```bash
uvicorn main:app --reload --port 8000
```

You should see: `Uvicorn running on http://127.0.0.1:8000`

API docs available at: http://127.0.0.1:8000/docs

---

## 4. Frontend setup

Open a **second terminal** in VS Code:

```bash
cd Frontend
```

### 4.1 Install dependencies

```bash
npm install
```

### 4.2 Create `.env` file

Create file `Frontend/.env` with:

```env
VITE_API_URL=http://localhost:8000
```

### 4.3 Run the frontend

```bash
npm run dev
```

You should see: `Local: http://localhost:5173/`

Open http://localhost:5173 in your browser.

---

## 5. First use

1. **Register a therapist** — click "Register", fill in name/email/password, select role **therapist**
2. **Login as therapist** — create tests, add questions with scores (0-5 points per option)
3. **Register a worker** — create another account with role **worker**
4. **Login as worker** — take tests, write journal entries, chat with AI assistant

---

## Troubleshooting

### `column test_results.test_id does not exist`
Your database has old schema. Reset it:
```sql
\c wellbeing
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
```
Then restart the backend.

### `ModuleNotFoundError: No module named 'xxx'`
Make sure the virtual environment is activated:
```bash
cd backend/src
venv\Scripts\activate
pip install -r ../requirements.txt
```

### `openai.AuthenticationError`
Check that `OPENAI_API_KEY` in `backend/src/.env` is valid and has credits.

### Frontend shows blank page or API errors
Make sure `VITE_API_URL=http://localhost:8000` is set in `Frontend/.env` and the backend is running.

### `psycopg2` install fails on Windows
Install the binary version (already in requirements.txt):
```bash
pip install psycopg2-binary
```
