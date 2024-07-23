#!/bin/bash

# Run the image recognition experiment on the same image (porsche.jpg) 
# of different resolutions
# The image-recognition benchmark input.py accepts the first line of the
# val_map.txt file as the input image, so all we gotta do is modify it per run

resolutions=("96" "128" "224" "256" "512" "758" "1024")
PYTHON=~/serverless-benchmarks/python-venv/bin/python3
CONFIG=config/openwhisk.json
ACTUAL_ARGS="--config $CONFIG --deployment openwhisk --verbose --repetitions 1000"
RESULTS_FOLDER="image_resolution_results"
VAL_MAP_PATH="benchmarks-data/benchmarks-data-tmp/400.inference/411.image-recognition/fake-resnet/"

mkdir -p $RESULTS_FOLDER

for resolution in "${resolutions[@]}"; do
    echo "Running $resolution"
    NEW_IMAGE="$resolution"x"$resolution"-Porsche.jpg
    rm "$VAL_MAP_PATH"/val_map.txt
    # 817 is the class idx, irrelevant but kept for correctness
    echo "$NEW_IMAGE 817" > "$VAL_MAP_PATH"/val_map.txt
    $PYTHON sebs.py benchmark invoke 411.image-recognition test $ACTUAL_ARGS
    mv 411.image-recognition_experiments.json "$RESULTS_FOLDER"/$resolution.json
    echo "Sleeping for 60 seconds"
    sleep 60
done