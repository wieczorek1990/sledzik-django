#!/bin/sh
# Tests composing.

valid_token=cd08835b-caff-4f49-90ae-cdd477dcf8b2
authorization="898e3d257a0c159fb5a4e7839e9880e0a959362c"
id=1

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

url="localhost:8000/api/actions/1/hit/"
echo "Hit:"
http POST $url Authorization:"Token $authorization" token=$valid_token
