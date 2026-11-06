#!/bin/sh
# Runs tests.

set -eu

cd "$(dirname "$0")/.."

. ./.venv/bin/activate
./.venv/bin/python manage.py test "$@"
