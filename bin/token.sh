#!/bin/sh
# Token grabber.

http POST sledzik.soiree.tech/auth/token/ username=luke password=super | jq -r '.token'
