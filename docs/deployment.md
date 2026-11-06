# Deployment Guide

This guide covers deploying Śledzik to a Scaleway instance.

## Server Details

- **Server**: `root@sledzik.soiree.tech`
- **Domain**: `sledzik.soiree.tech`
- **Database**: SQLite
- **Stack**: Django + Daphne (ASGI) + Nginx + Let's Encrypt
- **Configuration**: Environment in `/etc/sledzik/sledzik.env` (chmod 600)

## Prerequisites

1. DNS record configured for `sledzik.soiree.tech`
2. SSH key-based access to `root@sledzik.soiree.tech` (passwordless)
3. `rsync` installed locally

## Quick Deploy

Run the master script from the project root:

```bash
chmod +x bin/deploy-all.sh
./bin/deploy-all.sh
```

This will:
1. Copy the code to the server via `rsync`
2. Provision the server (Python, Nginx, Certbot, firewall)
3. Deploy the app (virtualenv, dependencies, migrations, static files)
4. Set up SSL with Let's Encrypt and start services

## Manual Deploy (Step by Step)

If you prefer to run each step manually:

### 1. Provision the server

```bash
ssh root@sledzik.soiree.tech 'bash -s' < bin/provision.sh
```

This installs Python 3, Nginx, Certbot, configures the firewall, and creates the `sledzik` user.

### 2. Copy code to server

```bash
rsync -avz \
    --exclude='.venv' \
    --exclude='db.sqlite3' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='static/' \
    --exclude='.git/' \
    --exclude='.junie/' \
    --exclude='certificates/' \
    ./ root@sledzik.soiree.tech:/home/sledzik/sledzik-django/
```

### 3. Deploy the app

```bash
ssh root@sledzik.soiree.tech 'bash -s' < bin/deploy.sh
```

This sets up the Python virtual environment, installs dependencies, runs migrations, and collects static files.

### 4. Set up SSL and services

```bash
ssh root@sledzik.soiree.tech 'bash -s' < bin/setup-ssl.sh
```

This configures Nginx, obtains Let's Encrypt SSL certificates, and starts the Daphne service.

## Post-Deploy

### Create a superuser

```bash
ssh root@sledzik.soiree.tech 'su - sledzik -c "cd /home/sledzik/sledzik-django && .venv/bin/python manage.py createsuperuser"'
```

### Check service status

```bash
ssh root@sledzik.soiree.tech 'systemctl status sledzik'
ssh root@sledzik.soiree.tech 'systemctl status nginx'
```

### View logs

```bash
ssh root@sledzik.soiree.tech 'tail -f /var/log/sledzik/sledzik.log'
ssh root@sledzik.soiree.tech 'tail -f /var/log/sledzik/sledzik-error.log'
```

## Redeploy (after code changes)

After pushing code changes, just sync and restart:

```bash
# Sync code
rsync -avz \
    --exclude='.venv' \
    --exclude='db.sqlite3' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='static/' \
    --exclude='.git/' \
    --exclude='.junie/' \
    --exclude='certificates/' \
    ./ root@sledzik.soiree.tech:/home/sledzik/sledzik-django/

# Run migrations and restart
ssh root@sledzik.soiree.tech 'su - sledzik -c "cd /home/sledzik/sledzik-django && .venv/bin/pip install -r requirements.txt && .venv/bin/python manage.py migrate && .venv/bin/python manage.py collectstatic --noinput" && systemctl restart sledzik'
```

## File Structure

```
bin/
├── deploy-all.sh      # Master script (runs all steps)
├── provision.sh       # Server provisioning
├── deploy.sh          # App deployment
└── setup-ssl.sh       # SSL and service setup
config/
├── nginx/
│   └── sledzik.conf   # Nginx reverse proxy config
└── systemd/
    └── sledzik.service # systemd service for Daphne
```

## Troubleshooting

### SSL certificate issues

```bash
ssh root@sledzik.soiree.tech 'certbot renew --dry-run'
```

### Nginx config errors

```bash
ssh root@sledzik.soiree.tech 'nginx -t'
```

### Daphne not starting

```bash
ssh root@sledzik.soiree.tech 'journalctl -u sledzik -f'
```

### Database locked (SQLite)

If you see "database is locked" errors, ensure only one Daphne worker is running (the systemd service uses `-b 0` for threaded mode, which is safe for SQLite).
