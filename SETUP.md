# NutriSense AI — Setup Guide

Simple auth web app: **Login → Signup → Profile → Logout**, with user data stored in **SQLite** and passwords **encrypted (bcrypt)**.

## Project Structure

```
├── backend/          # FastAPI server
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   └── requirements.txt
├── frontend/         # React + Vite
│   ├── src/
│   │   ├── pages/    # Login, Signup, Profile
│   │   └── api/      # API calls
│   └── package.json
└── data/             # SQLite database (auto-created)
    └── users.db
```

---

## Step 1 — Install Python (if not installed)

Download Python 3.10+ from https://www.python.org/downloads/

Verify:

```bash
python --version
```

---

## Step 2 — Set up the Backend (FastAPI)

Open a terminal in the project root and run:

```bash
cd backend
python -m venv venv
```

**Windows (PowerShell):**

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Mac/Linux:**

```bash
source venv/bin/activate
pip install -r requirements.txt
```

Start the backend server:

```bash
uvicorn main:app --reload --port 8000
```

Backend runs at: **http://localhost:8000**

API docs: **http://localhost:8000/docs**

---

## Step 3 — Install Node.js (if not installed)

Download Node.js 18+ from https://nodejs.org/

Verify:

```bash
node --version
npm --version
```

---

## Step 4 — Set up the Frontend (React + Vite)

Open a **new terminal** (keep backend running) and run:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: **http://localhost:5173**

---

## Step 5 — Test the Application

1. Open **http://localhost:5173/login**
2. Click **Create account** → fill First name, Last name, Email, Password, Confirm password
3. Click **Create profile** → you are redirected to the profile page
4. Click **Logout** → you return to the login page
5. Sign in again with the same email and password

---

## Step 6 — Verify Database

After signup, check the SQLite file:

```
data/users.db
```

You can open it with [DB Browser for SQLite](https://sqlitebrowser.org/). The `users` table stores:

| Column           | Description                    |
|------------------|--------------------------------|
| id               | Auto-increment user ID         |
| first_name       | User first name                |
| last_name        | User last name                 |
| email            | Unique email                   |
| hashed_password  | **Encrypted** password (bcrypt)|
| created_at       | Registration timestamp         |

Passwords are **never stored in plain text** — only bcrypt hashes.

---

## API Endpoints

| Method | Endpoint      | Description              |
|--------|---------------|--------------------------|
| POST   | /api/signup   | Register new user        |
| POST   | /api/login    | Login with email/password|
| GET    | /api/me       | Get current user profile |

---

## Pages Flow

```
/login  ──(Create account)──►  /signup  ──(Create profile)──►  /profile  ──(Logout)──►  /login
   ▲                                                                                        │
   └──────────────────────────────(Sign in)─────────────────────────────────────────────────┘
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| CORS error | Ensure backend is on port 8000 and frontend on 5173 |
| `pip` not found | Use `python -m pip install -r requirements.txt` |
| Port already in use | Change port: `uvicorn main:app --reload --port 8001` |
| Email already registered | Use a different email or delete `data/users.db` to reset |

---

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy, SQLite, bcrypt (passlib), JWT
- **Frontend:** React 18, Vite, React Router
- **Database:** SQLite in `data/users.db`
