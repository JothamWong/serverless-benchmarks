#!/bin/bash

URL="http://d2l-data.s3-accelerate.amazonaws.com/aclImdb_v1.tar.gz"
FILENAME="aclImdb_v1.tar.gz"
EXTRACTED_DIR="aclImdb"
OUTPUT_DIR_ONE="benchmarks-data/benchmarks-data-tmp/600.chaining/603.content-moderation/"
OUTPUT_DIR_TWO="benchmarks-data/benchmarks-data-tmp/600.chaining/604.content-moderation-inline/"

echo "Downloading file..."
wget $URL -O $FILENAME

if [ $? -ne 0 ]; then
    echo "Download failed. Exiting..."
    exit 1
fi

echo "Extracting file..."
tar -xzf $FILENAME

if [ $? -ne 0 ]; then
    echo "Extraction failed. Exiting..."
    exit 1
fi

echo "Copying files..."

cp $EXTRACTED_DIR/test/pos/*.txt $OUTPUT_DIR_ONE
cp $EXTRACTED_DIR/test/pos/*.txt $OUTPUT_DIR_TWO

if [ $? -ne 0 ]; then
    echo "Copying files failed. Exiting."
    exit 1
fi

exit 0
