#!/bin/sh
# Tests composing.

set -euo pipefail

valid_token=$VALID_TOKEN
authorization=$AUTHORIZATION
id=$STARTING_ID

echo "Tenants:"
url_tenants="localhost:8000/admin/counting/tenant/add/"
read -p "Press enter to open tenants admin..."
open http://$url_tenants

echo "Projects:"
url_projects="localhost:8000/api/projects/"
http POST $url_projects Authorization:"Token $authorization" \
    name=soiree.tech tenant=$id

echo "Funnels:"
url_funnels="localhost:8000/api/funnels/"
http POST $url_funnels Authorization:"Token $authorization" \
    name=visits project=$id

echo "Actions:"
url_actions="localhost:8000/api/actions/"
http POST $url_actions Authorization:"Token $authorization" \
    name=ready funnel=$id

echo "Hit:"
url_hit="localhost:8000/api/actions/1/hit/"
http POST $url_hit Authorization:"Token $authorization" token=$valid_token
