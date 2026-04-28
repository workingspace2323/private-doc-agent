@echo off
REM ─────────────────────────────────────────────────────────────────────────────
REM start.bat — One-command launcher for Windows
REM Double-click this file or run from Command Prompt
REM ─────────────────────────────────────────────────────────────────────────────

title Private Document Agent

echo.
echo  ╔══════════════════════════════════════╗
echo  ║   🔒 Private Document Agent          ║
echo  ╚══════════════════════════════════════╝
echo.

REM ── Check Python ──────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  ❌ Python not found. Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

REM ── Create venv if needed ─────────────────────────────────────────────────
if not exist "venv\" (
    echo  📦 Creating virtual environment...
    python -m venv venv
)

REM ── Activate venv ─────────────────────────────────────────────────────────
call venv\Scripts\activate.bat

REM ── Install dependencies if needed ────────────────────────────────────────
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo  📥 Installing dependencies (first run only, may take a few minutes)...
    pip install -r requirements.txt -q
    echo  ✓ Dependencies installed
)

REM ── Check .env ────────────────────────────────────────────────────────────
if not exist ".env" (
    echo  ⚠️  Creating .env from template...
    copy .env.example .env
    echo.
    echo  ❗ IMPORTANT: Edit .env and add your ANTHROPIC_API_KEY
    echo     Open .env with Notepad and set:
    echo     ANTHROPIC_API_KEY=sk-ant-your-key-here
    echo.
    notepad .env
    pause
)

REM ── Check if vector store exists, ingest if not ───────────────────────────
if not exist "data\vectorstore\index.faiss" (
    echo  📚 Building document index (first run)...
    python main.py ingest
    if errorlevel 1 (
        echo  ❌ Ingestion failed. Check your documents folder and API key.
        pause
        exit /b 1
    )
    echo  ✓ Ingestion complete
) else (
    echo  ✓ Vector store found
)

REM ── Get IP for mobile display ─────────────────────────────────────────────
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set LOCAL_IP=%%a
    goto :got_ip
)
:got_ip
set LOCAL_IP=%LOCAL_IP: =%

echo.
echo  ╔═══════════════════════════════════════════════╗
echo  ║  🚀 Server starting...                        ║
echo  ╠═══════════════════════════════════════════════╣
echo  ║  Local:   http://localhost:8000               ║
echo  ║  Mobile:  http://%LOCAL_IP%:8000         ║
echo  ║  (Phone must be on same WiFi network)         ║
echo  ╚═══════════════════════════════════════════════╝
echo.
echo  Press Ctrl+C to stop the server.
echo.

REM ── Start server ──────────────────────────────────────────────────────────
uvicorn app:app --host 0.0.0.0 --port 8000 --log-level info

pause
