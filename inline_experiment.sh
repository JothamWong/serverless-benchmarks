#!/bin/bash

REPETITIONS=5000

# bash stop_minio.sh
# bash run_minio.sh
# make clear-cache
# wsk -i action delete upload-inline
# wsk -i action delete text-analysis-inline
# wsk -i action delete 604.content-moderation-inline-python-3.7
# python3 sebs.py benchmark invoke 604.content-moderation-inline test --config config/openwhisk.json --deployment openwhisk --verbose --repetitions $REPETITIONS
# curl -X DELETE 'http://localhost:9200/_all'
# bash stop_minio.sh

make clear-cache
wsk -i action delete upload
wsk -i action delete text-analysis
wsk -i action delete 603.content-moderation-python-3.7
bash run_minio.sh
python3 sebs.py benchmark invoke 603.content-moderation test --config config/openwhisk.json --deployment openwhisk --verbose --repetitions $REPETITIONS
bash stop_minio.sh
curl -X DELETE 'http://localhost:9200/_all'
