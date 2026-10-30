#!/bin/sh
# Trying...

set -euo pipefail

. ./bin/envs.sh
./manage.py collectstatic --noinput
./manage.py makemigrations
./manage.py migrate
./manage.py runserver 0.0.0.0
