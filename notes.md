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

## whisk stuff

```yaml
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

whisk:
  ingress:
    type: NodePort
    apiHostName: localhost
    apiHostPort: 31001
    useInternally: false

nginx:
  httpsNodePort: 31001

# disable affinity
affinity:
  enabled: false
toleration:
  enabled: false
invoker:
  options: "-Dwhisk.kubernetes.user-pod-node-affinity.enabled=false"
  # must use KCF as kind uses containerd as its container runtime
  containerFactory:
    impl: "kubernetes"

# This will install user-events, prometheus and grafana on cluster with already preconfigured grafana dashboards for visualizing user metrics
# grafana credentials are admin/admin
# https://<whisk.ingress.apiHostName>:<whisk.ingress.apiHostPort>/monitoring/dashboards
# Access prometheus with port forwarding
# kubectl port-forward svc/owdev-prometheus-server 9090:9090 --namespace openwhisk
metrics:
  prometheusEnabled: true
  userMetricsEnabled: true
```

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