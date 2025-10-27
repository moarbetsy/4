#!/bin/bash

# Camoufox Dashboard Setup Script
echo "🦊 Setting up Camoufox Anti-Detect Browser Dashboard..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed. Please install pip3."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
cd backend
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install firefox

# Check if Camoufox is available
echo "🦊 Checking Camoufox installation..."
python3 -c "
try:
    import camoufox
    print('✅ Camoufox is available')
except ImportError:
    print('⚠️ Camoufox not found. Installing from PyPI...')
    import subprocess
    subprocess.run(['pip', 'install', 'camoufox'])
    print('✅ Camoufox installed')
"

# Check if BrowserForge is available
echo "🔧 Checking BrowserForge installation..."
python3 -c "
try:
    import browserforge
    print('✅ BrowserForge is available')
except ImportError:
    print('⚠️ BrowserForge not found. Installing from PyPI...')
    import subprocess
    subprocess.run(['pip', 'install', 'browserforge'])
    print('✅ BrowserForge installed')
"

cd ..

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p data

# Set permissions
echo "🔐 Setting permissions..."
chmod +x run.sh
chmod +x setup.sh

echo "✅ Setup complete!"
echo ""
echo "🚀 To start the Camoufox Dashboard:"
echo "   ./run.sh"
echo ""
echo "🌐 The dashboard will be available at:"
echo "   http://localhost:12000"
echo ""
echo "📖 API documentation will be available at:"
echo "   http://localhost:12000/docs"