#!/bin/bash
# Provision the Scaleway server with all dependencies.
# Run as root: ssh root@151.115.72.64 'bash -s' < bin/provision.sh

set -eu

DOMAIN="sledzik.soiree.tech"

echo "=== Provisioning server for ${DOMAIN} ==="

# Update system
echo "-- Updating system packages..."
dnf update -y

# Install Python and dependencies
echo "-- Installing Python and dependencies..."
dnf install -y \
    python3 \
    python3-pip \
    git \
    curl \
    nginx \
    certbot

# Configure firewall
echo "-- Configuring firewall..."
if command -v firewall-cmd &>/dev/null; then
    echo "  Using firewalld..."
    firewall-cmd --permanent --add-service=ssh
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --reload
elif command -v iptables &>/dev/null; then
    echo "  Using iptables (firewalld not available)..."
    iptables -A INPUT -p tcp --dport 22 -j ACCEPT
    iptables -A INPUT -p tcp --dport 80 -j ACCEPT
    iptables -A INPUT -p tcp --dport 443 -j ACCEPT
else
    echo "  Warning: No firewall tool found. Please configure firewall manually."
fi

# Create app user (non-root)
echo "-- Creating app user..."
if ! id -u sledzik &>/dev/null; then
    useradd -m -s /bin/bash sledzik
fi

# Create app directory (in /opt to avoid SELinux home directory restrictions)
APP_DIR="/opt/sledzik"
mkdir -p "$APP_DIR"
chown sledzik:sledzik "$APP_DIR"

# Create logs directory
mkdir -p /var/log/sledzik
chown sledzik:sledzik /var/log/sledzik

echo "=== Provisioning complete ==="
echo "Next steps:"
echo "1. Deploy the app: ssh root@151.115.72.64 'bash -s' < bin/deploy.sh"
echo "2. Set up SSL: ssh root@151.115.72.64 'bash -s' < bin/setup-ssl.sh"
