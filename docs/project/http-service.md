# HTTP service and Docker

The CLI is still the main surface. This page is the optional local HTTP wrapper around the same engine: `POST /anonymize`, `POST /deanonymize`, `POST /verify`, `POST /report`. There is **no authentication**. Bind to this machine or a compose network.

Package version **0.24.0**. The HTTP layer is `pdf-anonymizer-api`. It depends on `pdf-anonymizer-core` only, not the CLI.

---

## Install and run

```bash
pip install pdf-anonymizer-api
pdf-anonymizer-api --host 127.0.0.1 --port 8000
```

The HTTP package depends on **core only**. It does not import the CLI.

`--host` defaults to `127.0.0.1` so other machines cannot connect. `--host 0.0.0.0` is for a container that compose then publishes on localhost.

OpenAPI docs: `http://127.0.0.1:8000/docs`.

### Docker

```bash
docker compose -f packages/pdf-anonymizer-api/docker-compose.yml up --build
curl http://127.0.0.1:8000/health
```

Dockerfile, compose, and the optional AppArmor profile live in `packages/pdf-anonymizer-api/`. Compose sets the build context to the repository root so the image can copy `pdf-anonymizer-core` as well. The image installs those two packages only (no CLI).

`POST /anonymize` defaults to `use_llm: false` (regex-only), so the container works without API keys. Pass `use_llm: true` and a provider key in the environment if you want the language model.

The AppArmor profile is `packages/pdf-anonymizer-api/apparmor/docker-anonymizer`. It is not enabled in compose. Load it on the host first, then add `security_opt: ["apparmor:docker-anonymizer"]`. That is a starting point for untrusted PDFs. It is not a complete sandbox.

---

## Endpoints

| Method | Path | What it does |
|---|---|---|
| `GET` | `/health` | `{"status": "ok", "version": "0.24.0"}` |
| `POST` | `/anonymize` | Mask a string. Returns text, mapping, and the entity list. |
| `POST` | `/deanonymize` | Put originals back from a mapping. |
| `POST` | `/verify` | Residual leftover scan. Does not rewrite. |
| `POST` | `/report` | Linkage-risk score. Does not rewrite. |

Bodies are JSON. There is no file-upload path. Send extracted text. Size limit: 5,000,000 characters.

### `POST /anonymize`

Default is regex-only (`use_llm: false`, `use_ner: false`, `min_confidence: 0`). That is a **service** default so Docker works without keys. The CLI `run` command is unchanged (`best-speed` still calls a language model unless you pass `--no-llm`).

```bash
curl -s http://127.0.0.1:8000/anonymize \
  -H 'content-type: application/json' \
  -d '{"text":"Pay DE89370400440532013000 to ada@example.com","use_llm":false}'
```

Response shape:

```json
{
  "anonymized_text": "Pay IBAN_1 to EMAIL_1",
  "mapping": {
    "DE89370400440532013000": "IBAN_1",
    "ada@example.com": "EMAIL_1"
  },
  "entities": [
    {
      "text": "DE89370400440532013000",
      "type": "IBAN",
      "base_form": "DE89370400440532013000",
      "score": 0.95,
      "source": "regex"
    },
    {
      "text": "ada@example.com",
      "type": "EMAIL",
      "base_form": "ada@example.com",
      "score": 0.85,
      "source": "regex"
    }
  ]
}
```

`source` is which **recognizer** proposed the span. `score` is that recognizer’s 0–1 hint. Neither is a calibrated probability. Full table: [Terminology](terminology.md#recognizer-source-and-score).

Optional body fields: `use_llm`, `use_ner`, `min_confidence`, `keep_list`, `deny_list`, `operators`, `seed_mapping`, `fake_secret`, `model_name`, `prompt_name` (`simple` / `detailed` / `hipaa`), `anonymized_entities`, `countries`.

### `POST /deanonymize`

```bash
curl -s http://127.0.0.1:8000/deanonymize \
  -H 'content-type: application/json' \
  -d '{"text":"Pay IBAN_1","mapping":{"DE89370400440532013000":"IBAN_1"}}'
```

The mapping may be original → stand-in (SDK direction) or stand-in → original (CLI file direction).

### `POST /verify` and `POST /report`

Same reports as `pdf-anonymizer verify` and `pdf-anonymizer report`. They do not rewrite the string. `verify` accepts `countries` and optional `use_llm` / `model_name`.

---

## Out of scope

- Authentication, TLS, and multi-tenant isolation. Put a reverse proxy in front if you need those.
- Spark / Ray / DuckDB UDFs.
- Uploading a PDF or Word file. Use the CLI `run` command for files.

---

## See also

- [Recognizer, source, and score](terminology.md#recognizer-source-and-score)
- [Drop low-score hits](recipes.md#drop-low-score-hits)
- [CLI Reference](cli-usage.md)
- [SDK & API Usage](api-usage.md)
