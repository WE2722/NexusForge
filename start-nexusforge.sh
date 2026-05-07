#!/bin/bash

echo "==================================================="
echo "            N E X U S F O R G E"
echo "==================================================="
echo ""
echo "Starting the NexusForge Application..."

# Start Backend in the background
echo "[1/2] Launching FastAPI Backend on Port 8000..."
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Start Frontend in the background
echo "[2/2] Launching React Frontend on Port 5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "NexusForge components are booting up!"
echo ""
echo "You can access the UI at: http://localhost:5173"
echo "You can access the API at: http://127.0.0.1:8000"
echo ""
echo "Press Ctrl+C to stop both servers."

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
