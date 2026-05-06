#!/bin/bash
# Test Connection Script for EnpiAI

echo "1. Testing System Health..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health
echo " (Expected: 200)"

echo "2. Testing Auth Login Endpoint (OPTIONS)..."
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS http://localhost:5000/api/auth/login)
echo "Status: $CODE (Expected: 200)"

if [ "$CODE" == "200" ]; then
    echo "✅ Backend is ONLINE and Routes are CORRECT."
    echo "If Frontend fails, run: cd frontend && npm run build && npm start"
else
    echo "❌ Backend Error. Check python app.py logs."
fi
