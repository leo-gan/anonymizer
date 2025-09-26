#!/usr/bin/env bash
set -euo pipefail

# Move to repo root (run is in scripts/)
cd "$(dirname "$0")/.."

# Run the anonymizer main module on the sample PDF
python3 -m pdf_anonymizer.main run tests/data/sample.pdf tests/data/sample_2.pdf --characters-to-anonymize=900000 --prompt-name=detailed --model-name=gemini-2.5-flash-lite

# Download sample PDF from https://arxiv.org/pdf/2506.16406v1.pdf
#python3 -m pdf_anonymizer.main run tests/data/2506.16406v1.pdf
