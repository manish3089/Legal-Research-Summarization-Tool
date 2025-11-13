@echo off
echo Starting Legal Document Summarization Tool...
echo.

REM Start Flask backend in a new window
start "Flask Backend" cmd /k "cd /d "%~dp0backend" && python app.py"

REM Wait 5 seconds for backend to initialize
timeout /t 5 /nobreak

REM Start Streamlit frontend in a new window
start "Streamlit Frontend" cmd /k "cd /d "%~dp0frontend" && streamlit run streamlit_app.py"

echo.
echo Both servers are starting...
echo Flask Backend: http://127.0.0.1:5000
echo Streamlit Frontend: http://localhost:8502
echo.
echo Press any key to close this window (servers will continue running)
pause >nul
