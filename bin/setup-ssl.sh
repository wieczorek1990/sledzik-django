#!/bin/bash
# Set up SSL certificates with Let's Encrypt and configure Nginx.
# Run as root after deploying the app: ssh root@sledzik.soiree.tech 'bash -s' < bin/setup-ssl.sh

set -eu

DOMAIN="sledzik.soiree.tech"
APP_DIR="/opt/sledzik"

echo "=== Setting up SSL for ${DOMAIN} ==="

# Create Certbot challenge directory
echo "-- Creating Certbot challenge directory..."
mkdir -p /var/www/certbot
# Fix SELinux context for Certbot webroot (required on Fedora)
semanage fcontext -a -t httpd_sys_content_t '/var/www/certbot(/.*)?' 2>/dev/null || true
restorecon -R /var/www/certbot

# Comment out default server block in nginx.conf (Fedora default catches all requests)
echo "-- Disabling default Nginx server block..."
if grep -q 'server_name  _;' /etc/nginx/nginx.conf; then
    cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak
    sed -i '/^    server {$/,/^    }$/s/^/    # /' /etc/nginx/nginx.conf
fi

# Copy Nginx config
echo "-- Installing Nginx configuration..."
cp ${APP_DIR}/config/nginx/sledzik.conf /etc/nginx/conf.d/sledzik.conf

# Remove default Nginx config if it exists
rm -f /etc/nginx/conf.d/default.conf

# Test Nginx config
echo "-- Testing Nginx configuration..."
nginx -t

# Reload Nginx
echo "-- Reloading Nginx..."
systemctl reload nginx

# Obtain SSL certificate using webroot method (more reliable than --nginx on Fedora)
echo "-- Obtaining SSL certificate from Let's Encrypt..."
certbot certonly --webroot -w /var/www/certbot \
    -d "$DOMAIN" \
    --non-interactive \
    --agree-tos \
    --register-unsafely-without-email \
    || echo "WARNING: Certbot failed. You may need to run it manually:"
    echo "  certbot certonly --webroot -w /var/www/certbot -d ${DOMAIN}"

# Allow Nginx to connect to backend port (SELinux)
echo "-- Configuring SELinux for Nginx backend access..."
semanage port -a -t http_port_t -p tcp 8000 2>/dev/null || semanage port -m -t http_port_t -p tcp 8000 2>/dev/null || true
setsebool -P httpd_can_network_connect 1 2>/dev/null || true

# Install systemd service
echo "-- Installing systemd service..."
cp ${APP_DIR}/config/systemd/sledzik.service /etc/systemd/system/sledzik.service
systemctl daemon-reload
systemctl enable sledzik
systemctl restart sledzik

echo "=== SSL setup complete ==="
echo "Your site should be accessible at: https://${DOMAIN}"
echo "Check service status: systemctl status sledzik"
echo "Check Nginx status: systemctl status nginx"
