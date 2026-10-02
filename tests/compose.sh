#!/bin/sh
# Tests composing.

valid_token="083a45de-be0c-479a-9870-806defe6799a"
authorization="4d7784131944de1a84433127feb0fd11b5711eac"
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
