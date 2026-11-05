#!/bin/bash
# Deploy the Śledzik Django app to the server.
# Run as root after provisioning: ssh root@151.115.72.64 'bash -s' < bin/deploy.sh
# Requires: repo accessible via git, or use rsync/scp to copy code first.

set -eu

DOMAIN="sledzik.soiree.tech"
APP_USER="sledzik"
APP_DIR="/home/${APP_USER}/sledzik-django"
VENV_DIR="${APP_DIR}/.venv"
SECRET_KEY_FILE="/etc/sledzik/secret_key"

echo "=== Deploying Śledzik to ${DOMAIN} ==="

# Create secrets directory
echo "-- Creating secrets directory..."
mkdir -p /etc/sledzik

# Generate secret key if it doesn't exist
if [ ! -f "$SECRET_KEY_FILE" ]; then
    echo "-- Generating Django secret key..."
    python3 -c "import secrets; print(secrets.token_urlsafe(50))" > "$SECRET_KEY_FILE"
    chmod 600 "$SECRET_KEY_FILE"
fi
SECRET_KEY=$(cat "$SECRET_KEY_FILE")

# Clone or update the repository
echo "-- Setting up application code..."
if [ -d "$APP_DIR/.git" ]; then
    cd "$APP_DIR"
    git pull origin main
else
    rm -rf "$APP_DIR"
    # If you have a private repo, set up SSH keys for the sledzik user first.
    # For now, we expect the code to be copied via rsync/scp.
    echo "WARNING: No git repo found at ${APP_DIR}."
    echo "Please copy the code to the server first:"
    echo "  rsync -avz --exclude='.venv' --exclude='db.sqlite3' --exclude='__pycache__' \\"
    echo "       --exclude='static/' --exclude='.git/' ./ sledzik@151.115.72.64:${APP_DIR}/"
    echo "Then re-run this script."
    exit 1
fi

chown -R "${APP_USER}:${APP_USER}" "$APP_DIR"

# Set up virtual environment
echo "-- Setting up Python virtual environment..."
su - "${APP_USER}" -c "python3 -m venv ${VENV_DIR}"
su - "${APP_USER}" -c "${VENV_DIR}/bin/pip install --upgrade pip"
su - "${APP_USER}" -c "${VENV_DIR}/bin/pip install -r ${APP_DIR}/requirements.txt"

# Create environment file
echo "-- Creating environment configuration..."
cat > "${APP_DIR}/bin/envs.sh" <<EOF
#!/bin/sh
export DJANGO_DEBUG="0"
export DJANGO_SECRET_KEY="${SECRET_KEY}"
export PORT="8000"
EOF
chown "${APP_USER}:${APP_USER}" "${APP_DIR}/bin/envs.sh"
chmod +x "${APP_DIR}/bin/envs.sh"

# Run migrations and collect static files
echo "-- Running migrations and collecting static files..."
su - "${APP_USER}" -c "cd ${APP_DIR} && ${VENV_DIR}/bin/python manage.py migrate --noinput"
su - "${APP_USER}" -c "cd ${APP_DIR} && ${VENV_DIR}/bin/python manage.py collectstatic --noinput"

# Create database backup directory
mkdir -p "${APP_DIR}/backups"
chown "${APP_USER}:${APP_USER}" "${APP_DIR}/backups"

echo "=== Deployment complete ==="
echo "Next steps:"
echo "1. Install systemd service: cp config/systemd/sledzik.service /etc/systemd/system/"
echo "2. Install Nginx config: cp config/nginx/sledzik.conf /etc/nginx/sites-available/"
echo "3. Set up SSL: ssh root@151.115.72.64 'bash -s' < bin/setup-ssl.sh"
echo "4. Start the service: systemctl enable --now sledzik"
