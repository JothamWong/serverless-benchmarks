#!/bin/bash

python3 generate_workload.py 0.005

nums=("1" "5" "10")
# nums=("1" "2" "3" "4" "5")

for num in "${nums[@]}"; do
    bash run_minio.sh
    make clear-cache
	python3 sebs.py open-close open-close --config config/openwhisk.json --deployment openwhisk --verbose --schedule_config generated_schedule.json --n_workers 10 --output-dir tmpscheduled --result_dir open_close-$num
    bash stop_minio.sh
    curl -X DELETE 'http://localhost:9200/_all'
done
