#!/bin/sh
# Token grabber.

http POST śledzik.pl:8000/auth/token/ username=luke password=super | jq -r '.token'
