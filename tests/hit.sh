#!/bin/sh
# Tests hitting.

not_present_token=
invalid_token="abcd"
valid_token="415037c0-9114-4cd3-9780-6f8872234730"
url="localhost:8000/api/counting/1/hit/"

function hit {
  token=$1
  echo "Testing token:"
  echo $token
  http POST $url token=$token
}

hit
hit $not_present_token
hit $invalid_token
hit $valid_token
