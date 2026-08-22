@echo off
setlocal enabledelayedexpansion
title Clinicon - Setup and Start
echo ============================================
echo    Clinicon - Setup and Start All Services
echo ============================================
echo.

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

:: ---- CLEANUP: Kill old Clinicon processes ----
echo [CLEANUP] Stopping old Clinicon services...
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":5000 " ^| findstr "LISTENING"') do taskkill /PID %%p /F >nul 2>&1
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":8100 " ^| findstr "LISTENING"') do taskkill /PID %%p /F >nul 2>&1
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":8200 " ^| findstr "LISTENING"') do taskkill /PID %%p /F >nul 2>&1
for /f "tokens=5" %%p in ('netstat -aon ^| findstr ":3000 " ^| findstr "LISTENING"') do taskkill /PID %%p /F >nul 2>&1
echo [OK] Old processes cleared.

:: ---- CLEANUP: Delete Python __pycache__ ----
echo [CLEANUP] Clearing Python cache...
for /d /r "%ROOT_DIR%" %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d" >nul 2>&1
)
echo [OK] Cache cleared.
echo.

:: ---- 0) Check Docker / Database ----
echo [0/7] Checking Database...
where docker >nul 2>&1
if errorlevel 1 goto :no_docker
    docker ps -q -f name=clinicon-db | findstr . >nul 2>&1
    if errorlevel 1 goto :start_docker
        echo [OK] PostgreSQL container already running.
        goto :docker_done
    :start_docker
        docker run -d --name clinicon-db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=12345 -e POSTGRES_DB=clinic_db -p 5432:5432 postgres:15 >nul 2>&1
        if errorlevel 1 docker start clinicon-db >nul 2>&1
        echo [OK] PostgreSQL started on port 5432.
        goto :docker_done
:no_docker
    echo [INFO] Docker not found. System will use SQLite / local database.
:docker_done
timeout /t 2 >nul

:: ---- 0b) Start Ollama (needed for Agent) ----
echo [0/7] Checking Ollama...
where ollama >nul 2>&1
if errorlevel 1 goto :no_ollama
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if errorlevel 1 goto :start_ollama
        echo [OK] Ollama already running.
        goto :ollama_done
    :start_ollama
        echo [SETUP] Starting Ollama...
        start "" ollama serve
        timeout /t 5 >nul
        goto :ollama_done
:no_ollama
    echo [WARN] Ollama not found! Agent chat will use default fallback mode.
:ollama_done

:: ---- 0c) Auto install python requirements ----
echo [0/7] Checking Python dependencies...
python -W ignore -c "import fastapi" >nul 2>&1
if errorlevel 1 goto :install_deps
    echo [OK] Python dependencies verified.
    goto :deps_done
:install_deps
    echo [SETUP] Installing Python requirements (first run)...
    pip install -r requirements.txt
:deps_done

:: 1) Backend (FastAPI - port 5000)
echo [1/5] Starting Backend on port 5000...
start "Clinicon-Backend" cmd /k "cd /d %ROOT_DIR%\hospital\hospital\clinic-backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload"
timeout /t 4 >nul

:: 2) RAG Server (port 8100)
echo [2/5] Starting RAG Server on port 8100...
start "Clinicon-RAG" cmd /k "cd /d %ROOT_DIR% && python rag_server.py"
timeout /t 3 >nul

:: 3) Agent Server (port 8200)
echo [3/5] Starting Agent Server on port 8200...
start "Clinicon-Agent" cmd /k "cd /d %ROOT_DIR% && python agent_server.py"
timeout /t 3 >nul

:: 4) Wait for Agent Server to be ready (it loads LangChain/ChromaDB which takes ~60s)
echo [4/5] Waiting for Agent Server to be ready (this may take up to 2 minutes)...
set AGENT_READY=0
for /l %%i in (1,1,24) do (
    if !AGENT_READY!==0 (
        curl -s http://localhost:8200/health >nul 2>&1
        if !errorlevel!==0 (
            set AGENT_READY=1
            echo [OK] Agent Server is ready!
        ) else (
            echo [...] Still loading... (attempt %%i/24)
            timeout /t 5 >nul
        )
    )
)
if !AGENT_READY!==0 (
    echo [WARN] Agent Server did not respond in time - Frontend will start anyway.
    echo [WARN] Chat may be unavailable for a few more moments.
)

:: 5) Frontend (Vite - port 3000)
echo [5/5] Starting Frontend on port 3000...
start "Clinicon-Frontend" cmd /k "cd /d %ROOT_DIR%\frontend && (if not exist node_modules npm install) && npm run dev"
timeout /t 3 >nul

echo.
echo ============================================
echo    All Clinicon services started successfully!
echo    - Backend:  http://localhost:5000
echo    - RAG:      http://localhost:8100
echo    - Agent:    http://localhost:8200
echo    - Frontend: http://localhost:3000
echo ============================================
pause
