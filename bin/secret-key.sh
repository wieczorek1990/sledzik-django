#!/bin/sh
# Coppier.

. ./.venv/bin/activate
secret_key=$(./bin/secret_key.py)

echo $secret_key | pbcopy
