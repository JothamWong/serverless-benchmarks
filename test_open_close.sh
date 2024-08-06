#!/bin/bash

run_open_close() {
    local scale=$1
    echo "$scale"
    # Clear cache, as updating function isn't really supported
    rm -rf cache/
    # If existing results
    rm -rf "open_close_$scale"
    python3 generate_workload.py --scale "$scale"
    python3 sebs.py open-close open-close --config config/openwhisk.json --deployment openwhisk --verbose --schedule_config generated_schedule.json --n_workers 10 --output-dir tmpscheduled --result_dir "open_close_$scale"
    python3 analyze_open_close.py --name "$scale"
}

scales=("0.01")
# scales=("0.001" "0.005" "0.01")

for scale in "${scales[@]}"; do
    run_open_close "$scale"
done