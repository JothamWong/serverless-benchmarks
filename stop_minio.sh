#!/bin/bash

# Find the container ID of the Minio container
container_id=$(docker ps | grep minio | awk '{print $1}')

# Check if a container was found
if [ -z "$container_id" ]
then
    echo "No Minio container found running"
else
    echo "Stopping Minio container with ID: $container_id"
    docker stop $container_id
    echo "Container stopped"
fi