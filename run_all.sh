#!/bin/bash

# This script runs all the individual benchmarks in a closed loop fashion
# To enable cold starts, allow the warm up phase
# To disable cold starts, comment out the warm up phase

set -e

PYTHON=~/serverless-benchmarks/python-venv/bin/python3
CONFIG=config/openwhisk.json
DEFAULT_RESULTS=experiments.json
RESULTS_FOLDER="host-results"
WARMUP_ARGS="--config $CONFIG --deployment openwhisk --verbose --repetitions 5"
ACTUAL_ARGS="--config $CONFIG --deployment openwhisk --verbose --repetitions 1000"

mkdir -p $RESULTS_FOLDER

run_experiment() {
    local benchmark=$1
    BENCHMARK_RESULTS="$benchmark"_"$DEFAULT_RESULTS"
    # echo "Warming up benchmark: $benchmark"
    # Comment out the warming up phase if you don't want to measure cold starts
    # Warm up results will be overridden
    # $PYTHON sebs.py benchmark invoke $benchmark test $WARMUP_ARGS
    # sleep 5
    echo "Running benchmark: $benchmark"
    $PYTHON sebs.py benchmark invoke $benchmark test $ACTUAL_ARGS
    mv $BENCHMARK_RESULTS $RESULTS_FOLDER/$BENCHMARK_RESULTS
}

run_experiment "110.dynamic-html"
run_experiment "120.uploader"
run_experiment "210.thumbnailer"
run_experiment "220.video-processing"
# run_experiment "311.compression"
run_experiment "411.image-recognition"
run_experiment "501.graph-pagerank"
run_experiment "502.graph-mst"
run_experiment "503.graph-bfs"

benchmarks=("110.dynamic-html"
            "120.uploader"
            "210.thumbnailer"
            "220.video-processing"
            "311.compression"
            "411.image-recognition"
            "501.graph-pagerank"
            "502.graph-mst"
            "503.graph-bfs")

#for exp in "${benchmarks[@]}"; do
#    run_experiment $exp
#    sleep 60
#done
