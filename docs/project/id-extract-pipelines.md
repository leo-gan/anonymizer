---
description: Guide for data, fintech, and security engineers using id-extract standalone for ReDoS-safe structured PII detection in logs, ETL, CI gates, and Microsoft Presidio pipelines.
---

# `id-extract` in Data & Security Pipelines

Data, fintech, and security engineers often need deterministic structured PII detection (IBANs, payment cards, tax/national IDs, emails, IPs) in CI gates, log scrubbers, serverless functions, or ETL jobs where installing PyTorch or `spaCy` is unacceptable.

`id-extract` depends only on `google-re2` (guaranteed linear-time matching, immune to catastrophic backtracking / ReDoS), covers **38 countries** with **26 check-digit validators**, and returns exact character spans without modifying text.

```bash
pip install id-extract
```

---

## 1. Country Scoping and Checksum Thresholds

Default `countries="all"` loads every bundled country's patterns. In production logs or regional datasets, **always scope `countries=`** to the jurisdictions relevant to your users to eliminate cross-country alphanumeric collisions (see [Check-Digit Algorithms](../id-extract/checksums.md)):

```python
from id_extract import extract

def find_structured_pii(
    text: str,
    countries: list[str],
    min_score: float = 0.80,
) -> list[dict]:
    """Return high-confidence structured hits (dropping TYPE_LIKE checksum failures at 0.55)."""
    hits = extract(text, countries=countries)
    return [h for h in hits if h["score"] >= min_score]

# Verified IBAN (score 0.95) and email (score 0.85) are kept;
# failed-checksum IBAN_LIKE (score 0.55) is filtered when min_score=0.80.
hits = find_structured_pii(
    "Wire DE89370400440532013000 or notify ops@example.com",
    countries=["DE", "GB", "US"],
)
```

Score meanings:

- **`0.95`** — Pattern matched and mathematical check digit passed (Luhn, ISO 13616 mod-97, Verhoeff, weighted sums).
- **`0.85`** — Pattern matched for an identifier type with no standard check digit (email, phone, SSN, URL, IP).
- **`0.55`** — Pattern matched but check digit failed (`TYPE_LIKE`, e.g., `IBAN_LIKE`). Keep at `min_score=0.0` for privacy-first masking (so mistyped numbers stay hidden), or drop with `min_score=0.80` for low-noise alerting.

---

## 2. CI / Log-Leak Gate Example

Fail a CI step or pre-publish check if structured PII appears in exported logs or sample fixtures:

```python
import pathlib
import sys
from id_extract import extract

def scan_files(paths: list[str], countries: list[str]) -> int:
    leaks = 0
    for path in paths:
        content = pathlib.Path(path).read_text(encoding="utf-8", errors="ignore")
        for hit in extract(content, countries=countries):
            if hit["score"] >= 0.85:
                print(f"{path}:{hit['start']}-{hit['end']} {hit['type']}")
                leaks += 1
    return 1 if leaks else 0

if __name__ == "__main__":
    sys.exit(scan_files(sys.argv[1:], countries=["US", "GB", "DE"]))
```

Notice that the script logs only the file path, character offset, and `type` — **never the matched raw value** — so CI logs do not become a secondary leak surface.

---

## 3. Using `id-extract` Inside Microsoft Presidio

Teams already running [Microsoft Presidio](https://microsoft.github.io/presidio/) can register `id-extract` as a custom `EntityRecognizer` to gain ReDoS-safe 38-country national IDs and check-digit validators alongside Presidio's NER pipeline:

```python
from id_extract import extract
from presidio_analyzer import EntityRecognizer, RecognizerResult

class IdExtractRecognizer(EntityRecognizer):
    """Bridge id-extract's RE2 + checksum catalog into Presidio AnalyzerEngine."""

    def __init__(self, countries: list[str], supported_entities: list[str]):
        super().__init__(
            supported_entities=supported_entities,
            name="IdExtractRecognizer",
            supported_language="en",
        )
        self.countries = countries

    def load(self) -> None:
        pass

    def analyze(self, text, entities, nlp_artifacts=None):
        requested = set(entities) if entities else set(self.supported_entities)
        results = []
        for hit in extract(text, countries=self.countries):
            if hit["type"] in requested:
                results.append(
                    RecognizerResult(
                        entity_type=hit["type"],
                        start=hit["start"],
                        end=hit["end"],
                        score=hit["score"],
                    )
                )
        return results
```

---

## See Also

- [id-extract Overview](../id-extract/index.md) and [Install and API](../id-extract/api.md)
- [Check-Digit Algorithms](../id-extract/checksums.md) — mathematical overview and `STRICT_CHECKSUMS` vs. `TYPE_LIKE` policy
- [Country Catalog](../id-extract/countries/index.md) — 38 countries with official agency and statutory citations
- [Tool Comparison](tool-comparison.md) — comparing `id-extract` and `pdf-anonymizer` with Presidio and ARX
