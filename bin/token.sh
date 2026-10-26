#!/bin/sh
# Token grabber.

http POST sledzik.soiree.tech:8000/auth/token/ username=luke password=super | jq -r '.token'
