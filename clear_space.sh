#!/bin/bash
# Simple script to clear all existing data
bash stop_minio.sh
# Assumes that the elasticsearch docker container is up
curl -X DELETE 'http://localhost:9200/_all'