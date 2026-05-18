#!/bin/bash
# Start both backend and frontend

cd "$(dirname "$0")"

echo "Starting ICT Trading Dashboard..."

# Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACK_PID=$!
echo "Backend PID: $BACK_PID"

cd ../frontend
npm run dev &
FRONT_PID=$!
echo "Frontend PID: $FRONT_PID"

echo ""
echo "Dashboard running at: http://localhost:3000"
echo "API running at:       http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop both."

trap "kill $BACK_PID $FRONT_PID 2>/dev/null; exit" INT TERM
wait
