#!/bin/sh
# Resets the database.

. ./.venv/bin/activate
./manage.py reset_db --noinput
