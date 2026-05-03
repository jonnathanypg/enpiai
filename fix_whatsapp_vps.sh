#!/bin/bash
# ============================================================================
# fix_whatsapp_vps.sh
# EnpiAI — WhatsApp Gateway Repair Script for Contabo VPS
#
# This script resolves the ECONNRESET crash loop caused by PM2 running
# an outdated npx-based package instead of the local compiled code.
#
# Usage: ssh root@<VPS_IP> 'bash -s' < fix_whatsapp_vps.sh
#   or:  scp fix_whatsapp_vps.sh root@<VPS_IP>: && ssh root@<VPS_IP> bash fix_whatsapp_vps.sh
#
# Copyright © 2026 WEBLIFETECH (Jonnathan Peña). All Rights Reserved.
# ============================================================================

set -euo pipefail

PROJECT_DIR="/root/enpiai/api-whatsapp"
PM2_NAME="enpiai-whatsapp"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔧 EnpiAI WhatsApp Gateway — VPS Repair Script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ------------------------------------------------------------------
# Step 1: Stop and delete the old PM2 process
# ------------------------------------------------------------------
echo "🛑 Step 1: Stopping old PM2 process '${PM2_NAME}'..."
pm2 stop "${PM2_NAME}" 2>/dev/null || true
pm2 delete "${PM2_NAME}" 2>/dev/null || true
echo "   ✅ Old process removed."

# ------------------------------------------------------------------
# Step 2: Pull latest code and rebuild
# ------------------------------------------------------------------
echo ""
echo "📦 Step 2: Pulling latest code and rebuilding..."
cd "${PROJECT_DIR}"
git pull origin main
npm install --production=false
npm run build
echo "   ✅ TypeScript compiled to dist/"

# ------------------------------------------------------------------
# Step 3: Clean corrupted WhatsApp sessions from MySQL
# ------------------------------------------------------------------
echo ""
echo "🗄️  Step 3: Cleaning corrupted WhatsApp sessions..."
echo "   ⚠️  This will disconnect all active WhatsApp sessions."
echo "   You will need to re-scan the QR code from the dashboard."
echo ""

# Use the .env file to get DB credentials
if [ -f "${PROJECT_DIR}/.env" ]; then
    source "${PROJECT_DIR}/.env"
    
    if [ -n "${DB_HOST:-}" ] && [ -n "${DB_USER:-}" ] && [ -n "${DB_PASSWORD:-}" ] && [ -n "${DB_NAME:-}" ]; then
        mysql -h "${DB_HOST}" -u "${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}" \
            -e "DELETE FROM bailey_sessions; SELECT ROW_COUNT() AS 'Sessions purged';" \
            2>/dev/null && echo "   ✅ Sessions purged from MySQL." \
            || echo "   ⚠️  Could not connect to MySQL. Purge sessions manually:"
    else
        echo "   ⚠️  DB credentials not found in .env. Purge manually:"
    fi
else
    echo "   ⚠️  No .env file found. Purge sessions manually:"
fi
echo "       mysql -e \"DELETE FROM bailey_sessions;\" <your_db_name>"

# ------------------------------------------------------------------
# Step 4: Start the service with PM2 using the local compiled code
# ------------------------------------------------------------------
echo ""
echo "🚀 Step 4: Starting WhatsApp gateway with local dist/app.js..."
cd "${PROJECT_DIR}"
pm2 start dist/app.js \
    --name "${PM2_NAME}" \
    --watch false \
    --max-memory-restart 300M \
    --restart-delay 5000 \
    --max-restarts 10

pm2 save
echo "   ✅ PM2 process '${PM2_NAME}' started and saved."

# ------------------------------------------------------------------
# Step 5: Verify
# ------------------------------------------------------------------
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Repair Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Next steps:"
echo "  1. Open your EnpiAI dashboard"
echo "  2. Go to Channels → WhatsApp"
echo "  3. Scan the new QR code"
echo ""
echo "  To check logs:   pm2 logs ${PM2_NAME}"
echo "  To check status:  pm2 status"
echo ""
