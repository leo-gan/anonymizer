---
description: Guide for AI and RAG engineers using pdf-anonymizer-core and pdf-anonymizer-api to pseudonymize text and documents before external LLM calls and restore outputs locally.
---

# AI & RAG Pipelines

AI and RAG applications frequently process sensitive PDFs, Word contracts, and user queries through external LLM APIs (OpenAI, Anthropic, Google Gemini). Sending raw PII across that boundary creates GDPR/HIPAA and contract-confidentiality exposure, while irreversible redaction (`<REDACTED>`) breaks entity tracking in summaries and Q&A.

This guide shows two integration patterns: **in-memory Python** (`pdf-anonymizer-core`) and a **local Docker sidecar** (`pdf-anonymizer-api`).

---

## Pattern 1: In-Memory Python Round-Trip (No Disk Artifacts)

When masking retrieved RAG chunks or user prompts in memory, call `anonymize_text_content` locally (using RE2 + optional local GLiNER NER or Ollama), send only the masked text to your frontier LLM, and restore placeholders with `restore_placeholders_in_text`:

```python
from pdf_anonymizer_core.conf import filter_regex_patterns
from pdf_anonymizer_core.core import anonymize_text_content
from pdf_anonymizer_core.utils import (
    mapping_to_placeholder_original,
    restore_placeholders_in_text,
)

raw_chunk = (
    "Dr. Elena Rostova (elena@clinic.example, IBAN DE89370400440532013000) "
    "approved the transfer on 2026-04-12."
)

# 1. Mask locally (use_llm=False + use_ner=True uses local RE2 + CPU GLiNER)
masked_text, mapping = anonymize_text_content(
    full_text=raw_chunk,
    text_pages=[raw_chunk],
    prompt_template="",
    model_name="",
    regex_patterns=filter_regex_patterns(["DE", "US"]),
    use_llm=False,
    use_ner=True,   # requires pip install "pdf-anonymizer-core[ner]"
)

# 2. Send ONLY `masked_text` to your external LLM (OpenAI / Anthropic / Gemini)
# Instruct the model to preserve placeholder tokens verbatim (e.g., PERSON_1, IBAN_1).
llm_response = f"Summary: {masked_text}"

# 3. Restore placeholders locally in memory
placeholder_to_original = mapping_to_placeholder_original(mapping)
restored_response, used_keys = restore_placeholders_in_text(
    llm_response, placeholder_to_original
)
```

### Multi-chunk / Multi-turn Consistency

Pass `seed_mapping=mapping` into subsequent `anonymize_text_content(...)` calls within the same user session or RAG batch so the same person keeps the same placeholder (`PERSON_1`) across both the user query and every retrieved document chunk.

### Reducing LLM Placeholder Drift

LLMs occasionally rephrase tokens (`PERSON_1` → `Person 1`) if not instructed clearly. Include one explicit rule in your downstream system prompt:

> *Preserve all typed stand-in tokens such as `PERSON_1`, `ORGANIZATION_2`, `EMAIL_1`, and `PERSON_1.v_1` verbatim in your output. Do not translate, reformat, or abbreviate them.*

---

## Pattern 2: Local HTTP Sidecar (Docker / Non-Python Services)

For polyglot backends or gateway-level masking, run `pdf-anonymizer-api` on localhost or an internal Docker Compose network:

```bash
docker compose -f packages/pdf-anonymizer-api/docker-compose.yml up --build
```

Call `POST /anonymize` before the upstream LLM request and `POST /deanonymize` on the response:

```bash
# 1. Mask outbound text (defaults to regex-only; pass "use_ner": true if [ner] is installed)
curl -s http://127.0.0.1:8000/anonymize \
  -H 'content-type: application/json' \
  -d '{"text": "Wire DE89370400440532013000 to ada@example.com", "countries": ["DE", "US"]}'

# 2. Restore placeholders in the LLM reply
curl -s http://127.0.0.1:8000/deanonymize \
  -H 'content-type: application/json' \
  -d '{"text": "Transfer IBAN_1 confirmed for EMAIL_1.", "mapping": {"DE89370400440532013000": "IBAN_1", "ada@example.com": "EMAIL_1"}}'
```

!!! warning "Security boundary for `pdf-anonymizer-api`"
    `pdf-anonymizer-api` has **no built-in authentication or TLS**. Bind strictly to `127.0.0.1` or a private compose/VPC network behind an authenticated reverse proxy, and store session mappings in an encrypted short-TTL store (or in request memory only). See [HTTP Service & Docker](http-service.md).

---

## See Also

- [SDK & API Usage](api-usage.md) — file-level helpers (`anonymize_file`, `anonymize_tabular_file`, `anonymize_docx_file`)
- [HTTP Service & Docker](http-service.md) — full endpoint schema and AppArmor profile
- [Lecture 6: Pseudonymization & Crypto](../101/pseudonymization-crypto.md) — key custody and GDPR Art. 4(5) boundaries
