#!/bin/bash
# Set up SSL certificates with Let's Encrypt and configure Nginx.
# Run as root after deploying the app: ssh root@151.115.72.64 'bash -s' < bin/setup-ssl.sh

set -eu

DOMAIN="sledzik.soiree.tech"

echo "=== Setting up SSL for ${DOMAIN} ==="

# Create Certbot challenge directory
echo "-- Creating Certbot challenge directory..."
mkdir -p /var/www/certbot

# Copy Nginx config
echo "-- Installing Nginx configuration..."
cp /home/sledzik/sledzik-django/config/nginx/sledzik.conf /etc/nginx/conf.d/sledzik.conf

# Remove default Nginx config if it exists
rm -f /etc/nginx/conf.d/default.conf

# Test Nginx config
echo "-- Testing Nginx configuration..."
nginx -t

# Reload Nginx
echo "-- Reloading Nginx..."
systemctl reload nginx

# Obtain SSL certificate
echo "-- Obtaining SSL certificate from Let's Encrypt..."
certbot --nginx \
    -d "$DOMAIN" \
    --non-interactive \
    --agree-tos \
    --redirect \
    --hsts \
    --staple-ocsp \
    --email "admin@soiree.tech" \
    || echo "WARNING: Certbot failed. You may need to run it manually:"
    echo "  certbot --nginx -d ${DOMAIN}"

# Set up automatic renewal
echo "-- Configuring automatic certificate renewal..."
certbot renew --dry-run || echo "WARNING: Dry run failed. Check Certbot configuration."

# Install systemd service
echo "-- Installing systemd service..."
cp /home/sledzik/sledzik-django/config/systemd/sledzik.service /etc/systemd/system/sledzik.service
systemctl daemon-reload
systemctl enable sledzik
systemctl restart sledzik

echo "=== SSL setup complete ==="
echo "Your site should be accessible at: https://${DOMAIN}"
echo "Check service status: systemctl status sledzik"
echo "Check Nginx status: systemctl status nginx"
