# NutriSense AI — Auth Web App

AI-based nutritional assessment system with Login, Signup, Profile, and Logout.

## Project Structure

```
├── backend/                    # FastAPI + SQLite + bcrypt password encryption
│   ├── main.py                 # API routes (signup, login, profile)
│   ├── database.py             # SQLite connection
│   ├── models.py               # User table model
│   ├── schemas.py              # Request/response validation
│   ├── auth.py                 # Password hashing + JWT tokens
│   └── requirements.txt        # Python dependencies
│
├── frontend/                   # React + Vite
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx             # Routes: /login, /signup, /profile
│       ├── index.css           # NutriSense AI theme
│       ├── api/
│       │   └── api.js          # Backend API calls
│       └── pages/
│           ├── Login.jsx       # Email + Password + Sign in
│           ├── Signup.jsx      # First/Last name, Email, Password
│           └── Profile.jsx     # Empty page + Logout button
│
├── data/                       # SQLite database (auto-created on signup)
│   └── users.db                # Created after first user registers
│
└── SETUP.md                    # Full step-by-step setup guide
```

## Quick Start

**Terminal 1 — Backend:**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173/login**

See **SETUP.md** for detailed instructions.
