#!/bin/sh

hyperfine --shell bash --export-json hyperfine.json --runs 1000 'wsk -i action invoke 411.image-recognition-python-3.7 --result --param object "{\"model\": \"resnet50-19c8e357.pth\", \"input\": \"800px-Porsche_991_silver_IAA.jpg\"}" --param bucket "{\"bucket\": \"sebs-benchmarks-9594b98e\", \"input\": \"411.image-recognition-1-input\", \"model\": \"411.image-recognition-0-input\"}"'