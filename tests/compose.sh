#!/bin/sh
# Tests composing.

valid_token="415037c0-9114-4cd3-9780-6f8872234730"
authorization="16959c7c40c1588f04d7b6a0764fe42e559e6f83"

url_tenants="localhost:8000/api/tenants/"
url_projects="localhost:8000/api/projects/"
url_funnels="localhost:8000/api/funnels/"
url_actions="localhost:8000/api/actions/"

echo "Tenants:"
http POST $url_tenants Authorization:"Token $authorization" name=Soiree
echo "Projects:"
http POST $url_projects Authorization:"Token $authorization" name=soiree.tech tenant=1
echo "Funnels:"
http POST $url_funnels Authorization:"Token $authorization" name=visits project=1
echo "Actions:"
http POST $url_actions Authorization:"Token $authorization" name=ready funnel=1
