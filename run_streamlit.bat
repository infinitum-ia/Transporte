@echo off
REM Script to run Streamlit Chat Application
REM For Windows

echo ========================================
echo Transformas - Medical Transport Agent
echo Streamlit Chat Interface
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env file exists
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo Please create .env file with API configuration
    echo.
)

REM Check if API is running
echo Checking if API is running...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [WARNING] API is not running on http://localhost:8000
    echo Please start the API first with: uvicorn src.presentation.api.main:app --reload
    echo.
    echo Press any key to continue anyway or Ctrl+C to cancel...
    pause >nul
)

REM Start Streamlit
echo.
echo Starting Streamlit application...
echo Application will open in your browser at http://localhost:8501
echo.
echo Press Ctrl+C to stop the application
echo.

streamlit run app_streamlit.py

pause
