#!/bin/bash
# This script starts a container in the background and keeps it running
# so that you can use `docker exec` to run commands in it.
docker run -d --name pdf-anonymizer-test pdf-anonymizer:latest tail -f /dev/null
