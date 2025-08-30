#!/bin/bash
# Get the directory where the script is located
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Change to the project root directory (one level up from the script's directory)
cd "$SCRIPT_DIR/.."

# Now run the docker build command from the project root
docker build -t pdf-anonymizer:latest .
