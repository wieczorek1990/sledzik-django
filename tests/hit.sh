#!/bin/sh
# Tests hitting.

not_present_token=
invalid_token="abcd"
valid_token="6aa5ad33-7c0d-4b8a-a418-b13a13b56b4f"
url="localhost:8000/api/actions/1/hit/"

function hit {
  token=$1
  echo "Testing token: $token"

  http POST $url token=$token
}

hit
hit $not_present_token
hit $invalid_token
hit $valid_token
