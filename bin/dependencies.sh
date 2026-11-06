#!/bin/sh
# Installs dependencies.

. ./.venv/bin/activate
pip3 install -U -r requirements.txt
