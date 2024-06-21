SHELL := /bin/bash
MINIO-URL=10.90.36.41

gen-candidates:
	python3 generate_candidates.py

gen-schedule:
	python3 generate_workload.py

schedule:
	make clear-cache
	python3 sebs.py schedule run-schedule --config config/openwhisk.json --deployment openwhisk --verbose --schedule_config generated_schedule.json

# Simple check if can run a simple benchmark
test:
	make clear-cache
	python3 sebs.py benchmark invoke 110.dynamic-html test --config config/openwhisk.json --deployment openwhisk --verbose --repetitions 5 --trigger library

test-chain:
	make clear-cache
	-wsk -i action delete split
	-wsk -i action delete sort
	-wsk -i action delete 601.helloworld-python-3.7
	python3 sebs.py benchmark invoke 601.helloworld test --config config/openwhisk.json --deployment openwhisk --verbose --repetitions 5


# Workflow for testing chaining
dev-chaining:
	echo "booga"

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

# Literal first time initialization
start-deployment:
	make clear-cache
	make start-kind
	make deploy-whisk

restart-deployment:
	make clear-cache
	make tear-down-whisk
	make stop-kind
	make start-kind
	make deploy-whisk

set-cpu-freq:
	sudo cpupower -c 0-$$(( $$(nproc) - 1 )) frequency-set --min 2.5GHz --max 2.5Ghz -g performance