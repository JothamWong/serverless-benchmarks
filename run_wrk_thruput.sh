#!/bin/sh

OPENWHISK_PATH="/mnt/sdb/home/Jotham/openwhisk"
AUTH_FILE="${OPENWHISK_PATH}/ansible/files/auth.guest"
OUTPUT_DIR="./wrk_results"
URL="https://172.17.0.1"

AUTH_KEY=$(cat $AUTH_FILE)

run_throughput_test() {
    local concurrency=$1
    local action_concurrency=$2
    local threads=$3
    local duration=$4
    
    output_file="${OUTPUT_DIR}/${concurrency}_${action_concurrency}_${threadas}_${duration}.log"
    bash ./throughput.sh "$URL" "$AUTH_KEY" "$concurrency" "$action_concurrency" "$threads" "$duration" | tee "$output_file"
}

mkdir -p "$OUTPUT_DIR"

run_throughput_test 48 110 48 5s
# run_throughput_test 96 110 48 30s
# run_throughput_test 144 110 48 30s
# run_throughput_test 192 110 48 30s