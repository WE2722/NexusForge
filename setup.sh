#!/bin/bash
echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║       NexusForge First-Time Setup             ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed. Please install Python 3.10+."
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed. Please install Node.js 18+."
    exit 1
fi

# Backend setup
echo "[1/3] Setting up Python backend..."
cd backend
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
cd ..

# Frontend setup
echo "[2/3] Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Create .env
echo "[3/3] Checking configuration..."
if [ ! -f "backend/.env" ] && [ -f "backend/.env.example" ]; then
    cp backend/.env.example backend/.env
    echo "      Created backend/.env from .env.example"
    echo "      IMPORTANT: Edit backend/.env and add your API keys!"
fi

echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║       Setup Complete!                         ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Edit backend/.env with your API keys"
echo "  2. Run: ./start-nexusforge.sh"
