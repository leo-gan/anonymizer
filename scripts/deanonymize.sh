#!/usr/bin/env bash
set -euo pipefail

# Move to repo root (run is in scripts/)
cd "$(dirname "$0")/.."

SAMPLE="sample"

ANON="data/anonymized/$SAMPLE.anonymized.md"
MAP="data/mappings/$SAMPLE.mapping.json"

if [ ! -f "$ANON" ] || [ ! -f "$MAP" ]; then
  echo "Required files not found:"
  [ -f "$ANON" ] || echo " - Missing $ANON"
  [ -f "$MAP" ] || echo " - Missing $MAP"
  echo "Run scripts/run.sh first to generate anonymized output and mapping."
  exit 1
fi

pdf-anonymizer deanonymize "$ANON" "$MAP"
