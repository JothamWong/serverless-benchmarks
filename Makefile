SHELL := /bin/bash
PYTHON=python3
CONFIG=config/openwhisk.json
DEFAULT_RESULTS=experiments.json
RESULTS_FOLDER=results
ARGS=--config $(CONFIG) --deployment openwhisk --verbose --repetitions 100

dynamic-html:
	$(PYTHON) sebs.py benchmark invoke 110.dynamic-html test $(ARGS)
	mkdir -p $(RESULTS_FOLDER)
	mv $(DEFAULT_RESULTS) $(RESULTS_FOLDER)/dynamic-html.results.json

uploader:
	$(PYTHON) sebs.py benchmark invoke 120.uploader test $(ARGS)
	mkdir -p $(RESULTS_FOLDER)
	mv $(DEFAULT_RESULTS) $(RESULTS_FOLDER)/uploader.results.json

thumbnailer:
	$(PYTHON) sebs.py benchmark invoke 210.thumbnailer test $(ARGS)
	mkdir -p $(RESULTS_FOLDER)
	mv $(DEFAULT_RESULTS) $(RESULTS_FOLDER)/thumbnailer.results.json

video-processing:
	$(PYTHON) sebs.py benchmark invoke 220.video-processing test $(ARGS)
	mkdir -p $(RESULTS_FOLDER)
	mv $(DEFAULT_RESULTS) $(RESULTS_FOLDER)/video-processing.results.json

compression:
	$(PYTHON) sebs.py benchmark invoke 311.compression test $(ARGS)
	mkdir -p $(RESULTS_FOLDER)
	mv $(DEFAULT_RESULTS) $(RESULTS_FOLDER)/compression.results.json

image-recognition:
	$(PYTHON) sebs.py benchmark invoke 411.image-recognition test $(ARGS)
	mkdir -p $(RESULTS_FOLDER)
	mv $(DEFAULT_RESULTS) $(RESULTS_FOLDER)/image-recognition.results.json

graph-pagerank:
	$(PYTHON) sebs.py benchmark invoke 501.graph-pagerank test $(ARGS)
	mkdir -p $(RESULTS_FOLDER)
	mv $(DEFAULT_RESULTS) $(RESULTS_FOLDER)/graph-pagerank.results.json

graph-mst:
	$(PYTHON) sebs.py benchmark invoke 502.graph-mst test $(ARGS)
	mkdir -p $(RESULTS_FOLDER)
	mv $(DEFAULT_RESULTS) $(RESULTS_FOLDER)/graph-mst.results.json

graph-bfs:
	$(PYTHON) sebs.py benchmark invoke 503.graph-bfs test $(ARGS)
	mkdir -p $(RESULTS_FOLDER)
	mv $(DEFAULT_RESULTS) $(RESULTS_FOLDER)/graph-bfs.results.json


# Need to sleep to avoid openwhisk rate limiting
# TODO: Check how to override rate limiting
run-all: 
	make dynamic-html
	sleep 60 
	make uploader 
	sleep 60 
	make thumbnailer 
	sleep 60 
	make video-processing 
	sleep 60 
	make compression 
	sleep 60 
	make image-recognition 
	sleep 60 
	make graph-pagerank 
	sleep 60 
	make graph-mst 
	sleep 60 
	make graph-bfs

start-kind:
	./openwhisk-deploy-kube/deploy/kind/start-kind.sh;

tear-down-whisk:
	helm uninstall owdev -n openwhisk

deploy-whisk:
	helm install owdev ./openwhisk-deploy-kube/helm/openwhisk -n openwhisk --create-namespace -f openwhisk-deploy-kube/deploy/kind/mycluster.yaml;
	kubectl get pods -n openwhisk --watch

view-pods:
	kubectl get pods -n openwhisk --watch

clear-cache:
	rm -rf cache/