# RuralCare Connect

A college prototype for improving access to rural public healthcare services.

This project is bilingual (English and Marathi). Right now it has a React frontend, a FastAPI backend, a local SQLite database, and a public healthcare facility directory. There is no login, no referral APIs, and no dashboard yet.

## Folder layout

- `frontend` — React + Vite + Tailwind CSS
- `backend` — Python + FastAPI + SQLite (`ruralcare.db` is created locally)

## Prerequisites (Windows)

- Node.js and npm
- Python 3

## 1. Backend (PowerShell)

Open a PowerShell window in the project folder, then run:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\uvicorn.exe main:app --reload --host 127.0.0.1 --port 8001
```

The API will run at `http://127.0.0.1:8001`. This project uses port **8001** on purpose. On some Windows machines port 8000 is blocked (`WinError 10013`).

Health check: open `http://127.0.0.1:8001/api/v1/health` in a browser. You should see:

```json
{"status":"ok","app":"RuralCare Connect"}
```

Optional API docs (built into FastAPI): `http://127.0.0.1:8001/docs`

If PowerShell blocks virtual-environment activation, you do not need to activate it. The commands above call the `.venv` Python and Uvicorn files directly.

The first time the backend starts, it creates any missing SQLite tables. It does **not** delete existing records.

Optional: add a few clearly fictional demo facilities and services (safe to run more than once):

```powershell
.\.venv\Scripts\python.exe seed.py
```

Public facility directory:

- `GET http://127.0.0.1:8001/api/v1/facilities`
- Optional query parameters: `q`, `district`, `facility_type`, `service`
- `GET http://127.0.0.1:8001/api/v1/facilities/1`

Optional: confirm the tables can be created and queried:

```powershell
.\.venv\Scripts\python.exe test_database.py
.\.venv\Scripts\python.exe test_facilities.py
```

## 2. Frontend (PowerShell)

Open a **second** PowerShell window in the project folder, then run:

```powershell
cd frontend
npm install
npm run dev
```

The frontend will run at `http://localhost:5173`.

Keep both windows open while you develop: one for the backend, one for the frontend.

## Notes

- CORS is already configured so the local frontend (`http://localhost:5173` and `http://127.0.0.1:5173`) can call the backend on port 8001.
- The frontend API base URL is `http://127.0.0.1:8001/api/v1` (`VITE_API_BASE_URL` in `frontend/.env.example`).
- Local SQLite files (`*.db`, `*.sqlite`) and secret files (`.env`) are ignored by git.
- Do not commit the `backend/.venv` or `frontend/node_modules` folders.
