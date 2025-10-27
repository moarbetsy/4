#!/bin/bash

# Camoufox Dashboard Run Script
echo "🦊 Starting Camoufox Anti-Detect Browser Dashboard..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Change to backend directory
cd backend

# Check if all dependencies are installed
echo "📚 Checking dependencies..."
python3 -c "
import sys
required_modules = ['fastapi', 'uvicorn', 'camoufox', 'browserforge', 'playwright']
missing_modules = []

for module in required_modules:
    try:
        __import__(module)
    except ImportError:
        missing_modules.append(module)

if missing_modules:
    print(f'❌ Missing modules: {missing_modules}')
    print('Please run ./setup.sh to install dependencies.')
    sys.exit(1)
else:
    print('✅ All dependencies are installed')
"

if [ $? -ne 0 ]; then
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p ../logs

# Start the server
echo "🚀 Starting Camoufox Dashboard server..."
echo "🌐 Dashboard will be available at: http://localhost:12000"
echo "📖 API documentation at: http://localhost:12000/docs"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Run the FastAPI server with uvicorn
python3 -m uvicorn main:app --host 0.0.0.0 --port 12000 --reload --log-level info