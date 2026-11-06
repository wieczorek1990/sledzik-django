#!/bin/sh
# Trying...

set -euo pipefail

. ./.venv/bin/activate
. ./bin/envs.sh
./manage.py collectstatic --noinput
./manage.py makemigrations
./manage.py migrate
./manage.py runserver_plus 0.0.0.0:${PORT} --cert-file ./certificates/cert.crt --key-file ./certificates/cert.key
