#!/bin/sh
# Creates a superuser.

. ./.venv/bin/activate
./manage.py createsuperuser --username luke --email luke@soiree.tech --skip-checks
