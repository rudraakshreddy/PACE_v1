@echo off
echo Starting PROJECT PACE with PHREEQC Backend...

:: Check if virtual environment exists
if not exist venv\Scripts\activate (
    echo [INFO] First time setup: Creating virtual environment and installing dependencies...
    python -m venv venv
    call venv\Scripts\activate
    pip install fastapi uvicorn phreeqpython pydantic
) else (
    call venv\Scripts\activate
)

:: Start the Python backend in the background
echo [INFO] Starting Python backend server...
start /B python backend/server.py

:: Give the server a moment to spin up
timeout /t 3 /nobreak > nul

:: Open the frontend in the default browser
echo [INFO] Opening UI in browser...
start ui_ux_design\index.html

echo.
echo ========================================================
echo SERVER IS RUNNING ON http://localhost:8000
echo Leave this window open while using the application.
echo Close this window to stop the server.
echo ========================================================
pause
