#!/bin/sh
# Convenience command for setting up minio
ip=$(ip route get 8.8.8.8 | grep -oP 'src \K[^ ]+')
port=9011
python3 sebs.py storage start minio --port $port --output-json out_storage.json
jq --argfile file1 out_storage.json \
   ".deployment.openwhisk.storage = \$file1 | .deployment.openwhisk.storage.address = \"$ip:$port\"" \
   config/example.json > config/openwhisk.json
# verify that it worked, you should see http 200
make check-minio