#!/bin/sh

echo "With clear cache"
# Add --prepare to clear cache before each run
hyperfine --shell bash --export-json hyperfine_clear_cache.json --runs 10 --prepare "sync; sudo sh -c 'echo 1 > /proc/sys/vm/drop_caches'" 'wsk -i action invoke 411.image-recognition-python-3.7 --result --param object "{\"model\": \"resnet50-19c8e357.pth\", \"input\": \"800px-Porsche_991_silver_IAA.jpg\"}" --param bucket "{\"bucket\": \"sebs-benchmarks-9594b98e\", \"input\": \"411.image-recognition-1-input\", \"model\": \"411.image-recognition-0-input\"}"'


echo "Without clearing cache"
# Do a warm up of 1 first to get rid of the likely cold start
hyperfine --shell bash --export-json hyperfine_clear_cache.json --runs 10 --warmup 1 'wsk -i action invoke 411.image-recognition-python-3.7 --result --param object "{\"model\": \"resnet50-19c8e357.pth\", \"input\": \"800px-Porsche_991_silver_IAA.jpg\"}" --param bucket "{\"bucket\": \"sebs-benchmarks-9594b98e\", \"input\": \"411.image-recognition-1-input\", \"model\": \"411.image-recognition-0-input\"}"'