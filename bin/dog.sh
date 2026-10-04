#!/bin/sh
# Dog.

ruff check --fix --exclude '.*migrations.*' .
