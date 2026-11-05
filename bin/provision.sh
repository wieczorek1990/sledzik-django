#!/bin/bash
# Provision the Scaleway server with all dependencies.
# Run as root: ssh root@151.115.72.64 'bash -s' < bin/provision.sh

set -eu

DOMAIN="sledzik.soiree.tech"

echo "=== Provisioning server for ${DOMAIN} ==="

# Update system
echo "-- Updating system packages..."
apt-get update
apt-get upgrade -y

# Install Python and dependencies
echo "-- Installing Python and dependencies..."
apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    git \
    curl \
    nginx \
    certbot \
    python3-certbot-nginx \
    ufw

# Configure firewall
echo "-- Configuring firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
echo "y" | ufw enable

# Create app user (non-root)
echo "-- Creating app user..."
if ! id -u sledzik &>/dev/null; then
    useradd -m -s /bin/bash sledzik
fi

# Create app directory
APP_DIR="/home/sledzik/sledzik-django"
mkdir -p "$APP_DIR"
chown sledzik:sledzik "$APP_DIR"

# Create logs directory
mkdir -p /var/log/sledzik
chown sledzik:sledzik /var/log/sledzik

echo "=== Provisioning complete ==="
echo "Next steps:"
echo "1. Deploy the app: ssh root@151.115.72.64 'bash -s' < bin/deploy.sh"
echo "2. Set up SSL: ssh root@151.115.72.64 'bash -s' < bin/setup-ssl.sh"
