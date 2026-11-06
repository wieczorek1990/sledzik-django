#!/bin/sh
# Guard.

set -euo pipefail

. ./.venv/bin/activate
echo "Guard!"
./bin/style.sh
./bin/dog.sh
echo "Done."
