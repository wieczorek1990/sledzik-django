#!/bin/sh
# Tests hitting.

set -euo pipefail

not_present_token=
invalid_token="abcd"
valid_token=$VALID_TOKEN

url="localhost:8000/api/funnels/1/hit/"

function hit {
  token=$1
  echo "Testing token: $token"

  http POST $url token=$token
}

hit
hit $not_present_token
hit $invalid_token
hit $valid_token
