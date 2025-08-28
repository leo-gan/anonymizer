#!/usr/bin/env bash
set -euo pipefail

# Move to repo root (run is in scripts/)
cd "$(dirname "$0")/.."

# Run the anonymizer main module on the sample PDF
#python3 -m pdf_anonymizer.main deanonymize data/anonymized/sample.anonymized.md data/mappings/sample.mapping.json

# Download sample PDF from https://arxiv.org/pdf/2506.16406v1.pdf
python3 -m pdf_anonymizer.main deanonymize data/anonymized/2506.16406v1.anonymized.md data/mappings/2506.16406v1.mapping.json
