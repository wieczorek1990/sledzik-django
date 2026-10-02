#!/bin/sh
# Guard.

set -euo pipefail

echo "Guard!"
./bin/style.sh
./bin/dog.sh
echo "Done."
