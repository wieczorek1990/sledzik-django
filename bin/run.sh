#!/bin/sh
# Runner.

daphne -b 0.0.0.0 -p 8000 śledzik.asgi:application
