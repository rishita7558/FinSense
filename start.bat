@echo off
echo ==========================================================
echo Starting FinSense Financial Conversation Intelligence
echo ==========================================================
echo.

if not exist venv (
    echo [Error] Virtual environment not found. Please create it first.
    pause
    exit /b 1
)

:: Run the unified python startup script
.\venv\Scripts\python.exe start_app.py

pause
