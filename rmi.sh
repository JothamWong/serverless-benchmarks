#!/bin/bash

# This script removes all docker images, for some reason, docker image prune does not work well
# Get the list of repositories from docker image ls, excluding the header
repositories=$(docker image ls | awk 'NR>1 {print $1}' | sort -u)

# Loop through each repository and remove its images
for repo in $repositories; do
    echo "Removing images for repository: $repo"
    docker rmi --force $(docker images -q "$repo")
done

echo "Image removal process completed."
