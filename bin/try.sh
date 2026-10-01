#!/bin/sh
# Trying...

./manage.py collectstatic --noinput
./manage.py makemigrations
./manage.py migrate
./manage.py runserver
