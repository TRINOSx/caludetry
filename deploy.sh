#!/bin/bash
# =============================================================
# LASEM VOC Mesh AgriTech — Deployment Script
# Target: app.lifeandsemiconductors.com/agro/
# Server: 195.35.34.245:65002 (u387905082)
# =============================================================

set -e

# --- Configuration ---
REMOTE_USER="u387905082"
REMOTE_HOST="195.35.34.245"
REMOTE_PORT="65002"
REMOTE_DIR="~/voc-mesh-platform"
SSH_CMD="ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST}"
SCP_CMD="scp -P ${REMOTE_PORT}"

echo "============================================"
echo "  LASEM VOC Mesh — Deploy to Production"
echo "============================================"

# --- Step 1: Check SSH connectivity ---
echo ""
echo "[1/6] Testing SSH connection..."
${SSH_CMD} "echo 'SSH OK'" || {
    echo "ERROR: Cannot connect via SSH. Check credentials."
    exit 1
}

# --- Step 2: Check what's available on server ---
echo ""
echo "[2/6] Checking server capabilities..."
${SSH_CMD} << 'ENDSSH'
echo "--- System Info ---"
uname -a
echo ""
echo "--- Available tools ---"
which docker 2>/dev/null && docker --version || echo "Docker: NOT FOUND"
which docker-compose 2>/dev/null && docker-compose --version || echo "docker-compose: NOT FOUND"
which node 2>/dev/null && node --version || echo "Node: NOT FOUND"
which npm 2>/dev/null && npm --version || echo "npm: NOT FOUND"
echo ""
echo "--- Disk space ---"
df -h / | tail -1
echo ""
echo "--- Memory ---"
free -m | head -2
ENDSSH

# --- Step 3: Sync project files ---
echo ""
echo "[3/6] Syncing project files to server..."
rsync -avz --progress \
    -e "ssh -p ${REMOTE_PORT}" \
    --exclude='node_modules' \
    --exclude='.git' \
    --exclude='voc_training_internal' \
    --exclude='ml_training' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.env' \
    ./voc-mesh-platform/ \
    ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/

# --- Step 4: Create .env file on server ---
echo ""
echo "[4/6] Setting up environment..."
${SSH_CMD} << 'ENDSSH'
cd ~/voc-mesh-platform

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example — EDIT THIS FILE with real values!"
    echo "  nano ~/voc-mesh-platform/.env"
fi
ENDSSH

# --- Step 5: Deploy with Docker Compose ---
echo ""
echo "[5/6] Building and starting services..."
${SSH_CMD} << 'ENDSSH'
cd ~/voc-mesh-platform

# Build and start all services
docker compose build --no-cache dashboard nginx
docker compose up -d

# Wait for services to be ready
echo "Waiting for services..."
sleep 10

# Show status
docker compose ps
ENDSSH

# --- Step 6: Verify deployment ---
echo ""
echo "[6/6] Verifying deployment..."
${SSH_CMD} << 'ENDSSH'
echo "--- Service Status ---"
cd ~/voc-mesh-platform
docker compose ps

echo ""
echo "--- Dashboard health ---"
curl -s -o /dev/null -w "%{http_code}" http://localhost/agro/ || echo "Dashboard not responding"

echo ""
echo "--- API health ---"
curl -s http://localhost:8000/health || echo "API not responding"
ENDSSH

echo ""
echo "============================================"
echo "  Deployment complete!"
echo "  Dashboard: https://app.lifeandsemiconductors.com/agro/"
echo "============================================"
echo ""
echo "IMPORTANT: If this is the first deployment, edit .env:"
echo "  ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST}"
echo "  nano ~/voc-mesh-platform/.env"
echo "  cd ~/voc-mesh-platform && docker compose restart"
