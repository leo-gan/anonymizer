#!/bin/bash

CONTAINER_NAME="pdf-anonymizer-test"

# Check if the container exists
if [ $(docker ps -a -f name=^/${CONTAINER_NAME}$ --format '{{.Names}}') ]; then
    echo "Stopping and removing existing container: ${CONTAINER_NAME}"
    docker stop ${CONTAINER_NAME}
    docker rm ${CONTAINER_NAME}
fi

echo "Starting new container: ${CONTAINER_NAME}"
# This script starts a container in the background and keeps it running
# so that you can use `docker exec` to run commands in it.
docker run -d --name ${CONTAINER_NAME} pdf-anonymizer:latest tail -f /dev/null

echo "Container 'pdf-anonymizer-test' is now running in the background."
echo "You can access it using: docker exec -it pdf-anonymizer-test bash"
