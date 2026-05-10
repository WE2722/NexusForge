#!/bin/bash
echo ""
echo "Stopping NexusForge processes..."
echo ""

# Kill backend
echo "[1/2] Stopping backend (port 8000)..."
lsof -ti:8000 | xargs -r kill -9 2>/dev/null && echo "      Backend stopped." || echo "      No backend process found."

# Kill frontend
echo "[2/2] Stopping frontend (port 5173)..."
lsof -ti:5173 | xargs -r kill -9 2>/dev/null && echo "      Frontend stopped." || echo "      No frontend process found."

echo ""
echo "✓ All NexusForge processes stopped."
