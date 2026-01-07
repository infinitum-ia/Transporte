# PowerShell script to run Streamlit Chat Application
# For Windows PowerShell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Transformas - Medical Transport Agent" -ForegroundColor Cyan
Write-Host "Streamlit Chat Interface" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "[ERROR] Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    Write-Host "Then: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "Then: pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "[WARNING] .env file not found!" -ForegroundColor Yellow
    Write-Host "Please create .env file with API configuration" -ForegroundColor Yellow
    Write-Host ""
}

# Check if API is running
Write-Host "Checking if API is running..." -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction SilentlyContinue
    Write-Host "[OK] API is running" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] API is not running on http://localhost:8000" -ForegroundColor Yellow
    Write-Host "Please start the API first with:" -ForegroundColor Yellow
    Write-Host "  uvicorn src.presentation.api.main:app --reload" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press any key to continue anyway or Ctrl+C to cancel..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Start Streamlit
Write-Host ""
Write-Host "Starting Streamlit application..." -ForegroundColor Green
Write-Host "Application will open in your browser at http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the application" -ForegroundColor Yellow
Write-Host ""

streamlit run app_streamlit.py

Read-Host "Press Enter to exit"
