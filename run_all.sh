set -e

PYTHON=/mnt/sdb/home/Jotham/serverless-benchmarks/python-venv/bin/python3.10
CONFIG=config/openwhisk.json
DEFAULT_RESULTS=experiments.json
RESULTS_FOLDER="results"
WARMUP_ARGS="--config $CONFIG --deployment openwhisk --verbose --repetitions 10"
ACTUAL_ARGS="--config $CONFIG --deployment openwhisk --verbose --repetitions 1000"

mkdir -p $RESULTS_FOLDER

run_experiment() {
    local benchmark=$1
    echo "Warming up benchmark: $benchmark"
    # Warm up results will be overridden
    $PYTHON sebs.py benchmark invoke $benchmark test $WARMUP_ARGS
    sleep 4
    echo "Running benchmark: $benchmark"
    $PYTHON sebs.py benchmark invoke $benchmark test $ACTUAL_ARGS
	mv $DEFAULT_RESULTS $RESULTS_FOLDER/$benchmark.results.json
}

benchmarks=("110.dynamic-html"
            "120.uploader"
            "210.thumbnailer"
            "220.video-processing"
            "311.compression"
            "411.image-recognition"
            "501.graph-pagerank"
            "502.graph-mst"
            "503.graph-bfs")

for exp in "${benchmarks[@]}"; do
    run_experiment $exp
    sleep 60
done