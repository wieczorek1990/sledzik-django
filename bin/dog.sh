#!/bin/sh
# Dog.

. ./.venv/bin/activate
ruff check --exclude migrations --fix .
