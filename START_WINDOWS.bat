@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Install Python 3.12 or newer and enable Add Python to PATH.
  pause
  exit /b 1
)
where npm.cmd >nul 2>nul
if errorlevel 1 (
  echo Install Node.js 22 or newer, then reopen this file.
  pause
  exit /b 1
)
if not exist .env python scripts\setup.py
if not exist backend\.env (
  copy .env backend\.env >nul
  python -c "from pathlib import Path; p=Path('backend/.env'); p.write_text(p.read_text().replace('http://localhost:8080','http://localhost:5173'))"
)
if not exist backend\.venv\Scripts\python.exe python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install --upgrade pip
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
if errorlevel 1 goto failed
if not exist node_modules call npm.cmd install
if errorlevel 1 goto failed
cd backend
.venv\Scripts\python.exe -m alembic upgrade head
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m app.manage seed
cd ..
start "FlowOps API" cmd /k "cd /d %~dp0backend && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
start "FlowOps Frontend" cmd /k "cd /d %~dp0 && npm.cmd run dev:frontend"
echo.
echo Open http://localhost:5173 when the frontend says ready.
echo Login emails and password instructions are in README.md.
echo Close both terminal windows to stop FlowOps.
pause
exit /b 0
:failed
echo Setup could not finish. Read the error above and the README.
pause
exit /b 1
