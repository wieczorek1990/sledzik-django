#!/bin/sh
# Coppier.

secret_key=$(./bin/secret_key.py)

echo $secret_key | pbcopy
