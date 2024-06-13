SHELL := /bin/bash
MINIO-URL=10.90.36.41

start-kind:
	./openwhisk-deploy-kube/deploy/kind/start-kind.sh;

stop-kind:
	kind delete cluster --name kind

tear-down-whisk:
	helm uninstall owdev -n openwhisk

deploy-whisk:
	helm install owdev ./openwhisk-deploy-kube/helm/openwhisk -n openwhisk --create-namespace -f openwhisk-deploy-kube/deploy/kind/mycluster.yaml;
	kubectl get pods -n openwhisk --watch

view-pods:
	kubectl get pods -n openwhisk --watch

clear-cache:
	rm -rf cache/

check-minio:
	curl -i $(MINIO-URL):9011/minio/health/live

restart-deployment:
	make clear-cache
	make tear-down-whisk
	make stop-kind
	make start-kind
	make deploy-whisk

# set-cpu-freq:
# 	sudo cpupower -c 0-47 frequency-set --min 2.5GHz --max 2.5Ghz -g performance