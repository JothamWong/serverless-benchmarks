# Some stuff to note

## pip changes
urllib3<2
types-requests<2.31.0.7

## docker stuff

may need to set dns=8.8.8.8 for docker opts see: https://stackoverflow.com/questions/28668180/cant-install-pip-packages-inside-a-docker-container-with-ubuntu

change docker repository config to own personal one

## minio

use ip addr to find eno1 or wtv main ip card is, minio is exposed on network. `curl -i $addr/minio/health/live` to verify it works
minio used as "ephemeral storage" or s3 proxy

## wsk-cli

wsk cli auth must be set 
see two links

- https://github.com/apache/openwhisk-deploy-kube/blob/master/docs/k8s-kind.md
- https://github.com/apache/openwhisk-deploy-kube/

must wait for all pods to run first or will always encounter issues. pod spinning up might take about 2-5 mins?

## benchmarks that fail

504.dna-visualisation fails

2048mb memory limit for openwhisk deployment, might be too large
TODO: Find equivalent fn that meets deployment

## things to study or do

1. integrate with azure trace dataset
2. add more benchmarks from other suites if necessary
3. zipkin
4. qemu integration
5. find out how to integrate gem5 with this (probably very very difficult, so last prio)