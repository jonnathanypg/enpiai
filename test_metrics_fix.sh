#!/bin/bash
# Test Metrics Fix Script

EMAIL="test.distributor@example.com"
PASSWORD="Herbalife2026!"

echo "1. Logging in as $EMAIL..."
LOGIN_RES=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}")

# Extract Access Token (simple extraction for bash)
ACCESS_TOKEN=$(echo $LOGIN_RES | grep -o '"access_token": *"[^"]*"' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Login Failed. Response: $LOGIN_RES"
    exit 1
fi
echo "✅ Login Successful. Token acquired."

echo "2. Testing GET /api/dashboard/metrics..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  http://localhost:5000/api/dashboard/metrics)

echo "Response Status: $HTTP_CODE (Expected: 200)"

if [ "$HTTP_CODE" == "200" ]; then
    echo "✅ Dashboard Metrics Fixed! 🚀"
else
    echo "❌ Still failing. Check logs."
fi
