#!/usr/bin/env bash
set -euo pipefail

# Move to repo root (run is in scripts/)
cd "$(dirname "$0")/.."

# Ensure sample PDF exists; download if missing
# Download sample PDF from https://arxiv.org/pdf/2506.16406v1.pdf
# SAMPLE="tests/data/2506.16406v1.pdf"

SAMPLE="tests/data/sample.pdf"

# Run anonymization via CLI
# run with the default model
pdf-anonymizer run "$SAMPLE"

## run with the unknown model name for the google provider
#pdf-anonymizer run "$SAMPLE" --model-name "google/gemini-flash-latest"

## run with the gemini model name for the OpenRouter provider
#pdf-anonymizer run "$SAMPLE" --model-name "google/gemini-pro"
