SHELL := /bin/bash
MINIO-URL=10.90.36.41
OPENWHISK=/mnt/sdb/home/Jotham/openwhisk
API := $(shell cat /mnt/sdb/home/Jotham/openwhisk/ansible/files/auth.guest)

gen-candidates:
	python3 generate_candidates.py

gen-schedule:
	python3 generate_workload.py

schedule:
	make clear-cache
	python3 sebs.py schedule run-schedule --config config/openwhisk.json --deployment openwhisk --verbose --schedule_config generated_schedule.json --output-dir tmpscheduled --memory 128 --result_dir mem128

schedule-512:
	make clear-cache
	python3 sebs.py schedule run-schedule --config config/openwhisk.json --deployment openwhisk --verbose --schedule_config generated_schedule.json --output-dir tmpscheduled --memory 512 --result_dir mem512

schedule-1024:
	make clear-cache
	python3 sebs.py schedule run-schedule --config config/openwhisk.json --deployment openwhisk --verbose --schedule_config generated_schedule.json --output-dir tmpscheduled --memory 1024 --result_dir mem1024

wrk:
	bash $(OPENWHISK)/tests/performance/wrk_tests/throughput.sh https://172.17.0.1 $(API) $(OPENWHISK)/tests/performance/preparation/actions/noop.js 100 110 2 1s


# Simple check if can run a simple benchmark
test:
	python3 sebs.py benchmark invoke 411.image-recognition test --config config/openwhisk.json --deployment openwhisk --verbose --repetitions 10 --trigger library

test-2:
	python3 sebs.py benchmark invoke 120.uploader test --config config/openwhisk.json --deployment openwhisk --verbose --repetitions 1000 --trigger library

test-3:
	python3 sebs.py benchmark invoke 210.thumbnailer test --config config/openwhisk.json --deployment openwhisk --verbose --repetitions 1000 --trigger library

test-ml:
	make clear-cache
	-wsk -i action delete 411.image-recognition-python-3.7
	python3 sebs.py benchmark invoke 411.image-recognition test --config config/openwhisk.json --deployment openwhisk --verbose --repetitions 1000

test-chain:
	make clear-cache
	-wsk -i action delete upload
	-wsk -i action delete text-analysis
	-wsk -i action delete 603.content-moderation-python-3.7
	python3 sebs.py benchmark invoke 603.content-moderation test --config config/openwhisk.json --deployment openwhisk --verbose --repetitions 5

test-chain-inline:
	make clear-cache
	-wsk -i action delete upload-inline
	-wsk -i action delete text-analysis-inline
	-wsk -i action delete 604.content-moderation-inline-python-3.7
	python3 sebs.py benchmark invoke 604.content-moderation-inline test --config config/openwhisk.json --deployment openwhisk --verbose --repetitions 5

test-inline-transfer:
	make clear-cache
	-wsk -i action delete upload
	-wsk -i action delete text-analysis
	-wsk -i action delete 603.content-moderation-python-3.7
	python3 sebs.py benchmark invoke 603.content-moderation test --config config/openwhisk.json --deployment openwhisk --verbose --repetitions 10000

test-booga:
	make clear-cache
	-wsk -i action delete upload-inline
	-wsk -i action delete text-analysis-inline
	-wsk -i action delete 604.content-moderation-inline-python-3.7
	python3 sebs.py benchmark invoke 604.content-moderation-inline test --config config/openwhisk.json --deployment openwhisk --verbose --repetitions 10000


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

# This is needed because start-deployment doesnt guarantee that all components are fully init
configure-deployment:
	kubectl -n openwhisk  -ti exec owdev-wskadmin -- wskadmin limits set guest --invocationsPerMinute 10000
	kubectl -n openwhisk  -ti exec owdev-wskadmin -- wskadmin limits set guest --concurrentInvocations 10000
	kubectl -n openwhisk  -ti exec owdev-wskadmin -- wskadmin limits set guest --firesPerMinute 10000

configure-wsk-admin:
	$(OPENWHISK)/tools/admin/wskadmin limits set default --invocationsPerMinute 999999999999
	$(OPENWHISK)/tools/admin/wskadmin limits set guest --invocationsPerMinute 999999999999
	$(OPENWHISK)/tools/admin/wskadmin limits set default --firesPerMinute 999999999999
	$(OPENWHISK)/tools/admin/wskadmin limits set guest --firesPerMinute 999999999999
	$(OPENWHISK)/tools/admin/wskadmin limits set default --concurrentInvocations 999999999999
	$(OPENWHISK)/tools/admin/wskadmin limits set guest --concurrentInvocations 999999999999
	$(OPENWHISK)/tools/admin/wskadmin limits set default --maxActionConcurrency 999999999999
	$(OPENWHISK)/tools/admin/wskadmin limits set guest --maxActionConcurrency 999999999999

verify-deployment:
	kubectl -n openwhisk  -ti exec owdev-wskadmin -- wskadmin limits get guest 

restart-deployment:
	make clear-cache
	make tear-down-whisk
	make stop-kind
	make start-kind
	make deploy-whisk

set-cpu-freq:
	sudo cpupower -c 0-$$(( $$(nproc) - 1 )) frequency-set --min 2.5GHz --max 2.5Ghz -g performance