#!/bin/sh
# Runner.

set -eu

cd "$(dirname "$0")/.."

. ./bin/envs.sh
./manage.py collectstatic --noinput
exec daphne -e "ssl:${PORT}:interface=0.0.0.0:privateKey=./certificates/cert.key:certKey=./certificates/cert.crt" śledzik.asgi:application
