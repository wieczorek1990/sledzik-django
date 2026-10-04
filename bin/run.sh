#!/bin/sh
# Runner.

set -euo pipefail

. ./bin/envs.sh
./manage.py collectstatic --noinput
daphne -b 0.0.0.0 -p 8000 śledzik.asgi:application
