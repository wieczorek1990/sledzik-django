# Deployment Guide

This guide covers deploying Śledzik to a Scaleway instance.

## Server Details

- **Server**: `root@151.115.72.64`
- **Domain**: `sledzik.soiree.tech`
- **Database**: SQLite
- **Stack**: Django + Daphne (ASGI) + Nginx + Let's Encrypt

## Prerequisites

1. DNS `A` record for `sledzik.soiree.tech` pointing to `151.115.72.64`
2. SSH key-based access to `root@151.115.72.64` (passwordless)
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
ssh root@151.115.72.64 'bash -s' < bin/provision.sh
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
    ./ root@151.115.72.64:/home/sledzik/sledzik-django/
```

### 3. Deploy the app

```bash
ssh root@151.115.72.64 'bash -s' < bin/deploy.sh
```

This sets up the Python virtual environment, installs dependencies, runs migrations, and collects static files.

### 4. Set up SSL and services

```bash
ssh root@151.115.72.64 'bash -s' < bin/setup-ssl.sh
```

This configures Nginx, obtains Let's Encrypt SSL certificates, and starts the Daphne service.

## Post-Deploy

### Create a superuser

```bash
ssh root@151.115.72.64 'su - sledzik -c "cd /home/sledzik/sledzik-django && .venv/bin/python manage.py createsuperuser"'
```

### Check service status

```bash
ssh root@151.115.72.64 'systemctl status sledzik'
ssh root@151.115.72.64 'systemctl status nginx'
```

### View logs

```bash
ssh root@151.115.72.64 'tail -f /var/log/sledzik/sledzik.log'
ssh root@151.115.72.64 'tail -f /var/log/sledzik/sledzik-error.log'
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
    ./ root@151.115.72.64:/home/sledzik/sledzik-django/

# Run migrations and restart
ssh root@151.115.72.64 'su - sledzik -c "cd /home/sledzik/sledzik-django && .venv/bin/pip install -r requirements.txt && .venv/bin/python manage.py migrate && .venv/bin/python manage.py collectstatic --noinput" && systemctl restart sledzik'
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
ssh root@151.115.72.64 'certbot renew --dry-run'
```

### Nginx config errors

```bash
ssh root@151.115.72.64 'nginx -t'
```

### Daphne not starting

```bash
ssh root@151.115.72.64 'journalctl -u sledzik -f'
```

### Database locked (SQLite)

If you see "database is locked" errors, ensure only one Daphne worker is running (the systemd service uses `-b 0` for threaded mode, which is safe for SQLite).
