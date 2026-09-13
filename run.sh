#!/usr/bin/env bash
set -e

echo "========================================================"
echo "  RECON — Reconcile reality before taking action."
echo "========================================================"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Check Python environment
if [ ! -d "backend/.venv" ]; then
    echo "Creating Python virtual environment in backend/.venv..."
    python3 -m venv backend/.venv
    backend/.venv/bin/pip install -r backend/requirements.txt
fi

# Check frontend dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

echo ""
echo "Starting RECON Backend on http://127.0.0.1:8000..."
export PYTHONPATH="$ROOT_DIR/backend"
backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo "Starting RECON Frontend on http://localhost:5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd "$ROOT_DIR"

echo ""
echo "========================================================"
echo "  RECON Dashboard: http://localhost:5173"
echo "  API & Docs:      http://127.0.0.1:8000/docs"
echo "  Evaluation:      python evaluation/run_eval.py"
echo "========================================================"
echo "Press Ctrl+C to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM EXIT
wait
