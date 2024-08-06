#!/bin/bash

python3 generate_workload.py --scale 0.001

# nums=("2" "3" "4" "5" "6" "7" "8" "9" "10")
nums=("1" "2" "3" "4" "5")

for num in "${nums[@]}"; do
    bash run_minio.sh
    make clear-cache
    python3 sebs.py schedule run-schedule --config config/openwhisk.json --deployment openwhisk --verbose --schedule_config generated_schedule.json --output-dir tmpscheduled --result_dir scheduler-results-0.01-$num
    bash stop_minio.sh
    curl -X DELETE 'http://localhost:9200/_all'
done
