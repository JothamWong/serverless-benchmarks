#!/bin/bash

set -e
# scales=("0.001" "0.002" "0.003" "0.004" "0.005" "0.006" "0.007" "0.008" "0.009" "0.01")
scales=("0.005" "0.006" "0.007" "0.008" "0.009" "0.01")

echo "Running open"
# Open experiments
for scale in "${scales[@]}"; do
    bash run_minio.sh
    make clear-cache
    python3 generate_workload.py --scale $scale
    python3 sebs.py schedule run-schedule --config config/openwhisk.json --deployment openwhisk --verbose --schedule_config generated_schedule.json --output-dir tmpscheduled --result_dir open-results-scale-$scale
    bash stop_minio.sh
    curl -X DELETE 'http://localhost:9200/_all'
    sleep 60
done

for scale in "${scales[@]}"; do
    bash run_minio.sh
    make clear-cache
    python3 generate_workload.py --scale $scale
	python3 sebs.py open-close open-close --config config/openwhisk.json --deployment openwhisk --verbose --schedule_config generated_schedule.json --n_workers 10 --output-dir tmpscheduled --result_dir open_close-results-scale-$scale
    bash stop_minio.sh
    curl -X DELETE 'http://localhost:9200/_all'
    sleep 60
done