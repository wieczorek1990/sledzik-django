#!/bin/sh
# Token grabber.

http POST localhost:8000/auth/token/ username=luke password=super | jq -r '.token'
