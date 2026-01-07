#!/bin/bash
# Bash script to run Streamlit Chat Application
# For Unix/Mac/Linux

echo "========================================"
echo "Transformas - Medical Transport Agent"
echo "Streamlit Chat Interface"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -f "venv/bin/activate" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Please run: python -m venv venv"
    echo "Then: source venv/bin/activate"
    echo "Then: pip install -r requirements.txt"
    read -p "Press Enter to exit"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "[WARNING] .env file not found!"
    echo "Please create .env file with API configuration"
    echo ""
fi

# Check if API is running
echo "Checking if API is running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "[OK] API is running"
else
    echo "[WARNING] API is not running on http://localhost:8000"
    echo "Please start the API first with:"
    echo "  uvicorn src.presentation.api.main:app --reload"
    echo ""
    read -p "Press any key to continue anyway or Ctrl+C to cancel..."
fi

# Start Streamlit
echo ""
echo "Starting Streamlit application..."
echo "Application will open in your browser at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

streamlit run app_streamlit.py
