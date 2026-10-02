#!/bin/sh
# Trying...

-euo pipefail

./manage.py collectstatic --noinput
./manage.py makemigrations
./manage.py migrate
./manage.py runserver
