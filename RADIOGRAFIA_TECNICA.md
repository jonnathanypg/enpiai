# 🩻 EnpiAI - Technical X-Ray (Project Status Report)
**Date:** May 25, 2026
**Version:** 1.2.0 (Audit Update)
**Ownership:** WEBLIFETECH (Jonnathan Peña)

## 🏗️ 1. System Architecture Overview (Current)

The system has evolved into a **Unified Gateway Architecture** where FastAPI acts as the primary entry point, delegating to Flask for legacy routes.

- **Unified Gateway (FastAPI):** Port 5000. Handles async webhooks and routes.
- **Legacy Backend (Flask):** Integrated via `WSGIMiddleware` into FastAPI.
- **WhatsApp Gateway:** Node.js/TypeScript (Baileys) - Port 3001.
- **Frontend:** Next.js 16 (React 19) - Port 3000.
- **Database:** Remote MySQL (Hostinger: `82.197.82.185:3306`).
- **Cache/Queue:** Redis (Port 6381) - Used for Celery and potentially persistence.

---

## 🔍 2. Critical Audit Findings (May 25, 2026)

### 🔴 High Severity: WhatsApp Connection Instability
- **Issue:** `enpiai-api-whatsapp` logs show persistent `ECONNREFUSED` and `ETIMEDOUT` to the remote MySQL.
- **Root Cause:** Latency or connection limits on the remote MySQL server (`82.197.82.185`). 
- **Observation:** `nc -zv` shows the port is open, but the application pool fails frequently.
- **Impact:** WhatsApp messages fail to be saved/logged, and sessions are lost ("Intentional Logout" observed in logs).

### 🟡 Medium Severity: Health Endpoint 404
- **Issue:** `https://enpi.click/api/health` returns 404.
- **Root Cause:** Discrepancy between FastAPI route (`/health`) and Nginx routing/prefixing.
- **Impact:** Monitoring tools cannot verify system health.

---

## ✅ 3. Remediated Issues
- **Frontend Server Actions:** Missing `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` has been added to `frontend/.env`. Form submissions and interactive components are now functional.

---

## 🐍 4. Backend Deep Dive

### 🧠 Agent Orchestration & Compliance
- **Protocol Verification:** The mandatory `db.session.rollback()` is correctly implemented in `backend/routes/webhooks.py` and service entry points.
- **PII Protection:** Verified use of `EncryptedString` and `EncryptedJSON` in models (`Lead`, `Customer`, `Distributor`).
- **FastAPI-Flask Integration:** Successfully running under `a2wsgi`. FastAPI handles `/webhooks/whatsapp` asynchronously.

### 📜 Database Config
- **Python:** Using `pool_recycle: 300` and `pool_pre_ping: True` to mitigate remote DB drops.
- **Node.js:** Pool `connectionLimit: 5` with `enableKeepAlive: true`.

---

## 🔒 4. Security & Environment
- **Secrets:** Critical keys (OpenAI, Pinecone, PayPal) are present in `.env` files.
- **Resource Usage:** 
    - RAM: 9.2Gi Free (Excellent).
    - Disk: 180Gi Free (Excellent).
    - Uptime: 61 days.

---

## 🛠️ 5. Required Actions (Remediation)
1.  **Database:** Investigate remote MySQL logs for connection limit hits. Consider migrating to a local MySQL instance or a more robust RDS.
2.  **Secrets Rotation:** Rotate OpenAI and Pinecone keys as a precaution.

---

## 🚀 6. Updates (June 2026 CTO Audit)
- **Payment Gateway:** Successfully migrated from dLocal to **PayPal Advanced Credit and Debit Cards (ACDC)** for Subscriptions and Credit Blocks.
- **Critical Bug Fixes:** Resolved Priority 1 issues including CORS wildcard vulnerabilities, `gpt-4o-mini` LLM defaults, PDF newline escapes, and `is_o_model` detection.
- **Themes:** Added support for dynamic Light/Dark theme favicons in the UI.

