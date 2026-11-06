#!/bin/bash
# Master deployment script - runs all steps in order.
# Usage: ./bin/deploy-all.sh
# This script copies code to the server and runs provisioning, deployment, and SSL setup.

set -eu

SERVER="${1:-root@sledzik.soiree.tech}"
APP_DIR="/opt/sledzik"
DOMAIN="sledzik.soiree.tech"

cd "$(dirname "$0")/.."

echo "============================================"
echo "  Deploying Śledzik to ${DOMAIN}"
echo "  Server: ${SERVER}"
echo "============================================"

# Step 0: Add SSH key to agent
echo ""
echo "=== Step 0: Adding SSH key ==="
ssh-add

# Step 1: Create remote directory
echo ""
echo "=== Step 1: Creating remote directory ==="
ssh "${SERVER}" "mkdir -p ${APP_DIR}"

# Step 2: Copy code to server
echo ""
echo "=== Step 2: Copying code to server ==="
rsync -avz \
    --exclude='.venv' \
    --exclude='db.sqlite3' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='static/' \
    --exclude='.git/' \
    --exclude='.junie/' \
    --exclude='certificates/' \
    ./ "${SERVER}:${APP_DIR}/"

# Step 3: Provision server
echo ""
echo "=== Step 3: Provisioning server ==="
ssh "${SERVER}" "bash -s" < bin/provision.sh

# Step 4: Deploy app
echo ""
echo "=== Step 4: Deploying application ==="
ssh "${SERVER}" "bash -s" < bin/deploy.sh

# Step 5: Set up SSL and services
echo ""
echo "=== Step 5: Setting up SSL and services ==="
ssh "${SERVER}" "bash -s" < bin/setup-ssl.sh

echo ""
echo "============================================"
echo "  Deployment complete!"
echo "  Visit: https://${DOMAIN}"
echo "  Admin: https://${DOMAIN}/admin/"
echo "============================================"
