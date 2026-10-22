# Implementation plan: real-life use

**Status:** living plan
**Audience:** maintainers only
**Do not publish.** This directory is excluded from the MkDocs / GitHub Pages build (`exclude_docs` in `mkdocs.yml`). Do not link it from `README.md`, `docs/index.md`, or the public nav.

This plan continues [`improvement-plan.md`](improvement-plan.md). Items 1–26 there have shipped (v0.31.0). Item 27 (release hygiene) is absorbed here as item 3. It does not reopen OCR, native PDF, GLiNER, the HTTP service, or table *k*-anonymity as if they were missing. `docs/temp/` describes that older gap list and is not the backlog.

The product is a reversible document pseudonymizer. Personal values become typed stand-ins (`PERSON_1`) plus a mapping file. While the map exists, the file is still personal data. HIPAA and GDPR wording stays "aid", not a certificate.

## Progress

- [ ] 1. Publish NER and careful-LLM scores on the gold corpus
- [ ] 2. One local round-trip command (`relay`)
- [ ] 3. Security review of the local service (token, audit, no-telemetry, checksums)
- [ ] 4. Local review desk for span decisions
- [ ] 5. Clinical and legal profiles, with measured fixtures
- [ ] 6. Documents people actually have (OCR language, unreadable pages, PDF beside Markdown)
- [ ] 7. OpenAI-compatible proxy (deferred until 2 and 3 are in use)

## Why this order

Buyers compare leftover rate and recall. The only committed numbers are a regex-only run from package 0.17.0 (6,761 documents: mention F1 0.262, leftover 0.576, structured leftover 0.039). The public table still says the NER stage is not shipped. `span_ner.py` has shipped it. Item 1 fixes that record before any new claim.

The round-trip is the job the recipes already describe by hand: mask locally, send stand-in text out, restore the answer. A review desk and a PDF default matter after that path is one command and the restore endpoint is not anonymous.

Items 1, 2, and 3 can merge in any order. Item 4 waits on the token from item 3. Item 5 waits on the scorer from item 1. Item 6 waits on nothing, and should land after item 1 so the new language pages are scored the same way.

## Working rules

1. One item, one pull request, except item 6 which is two pulls because OCR honesty and the PDF default do not share a review.
2. `pdf-anonymizer run` keeps today's default unless the item says otherwise. Item 6 is the only default change, and it adds a file. It does not stop writing Markdown.
3. Do not claim legal compliance. New profiles are aids.
4. Do not add Tor, a live operating system, Spark, differential privacy on prose, audio or video, or a discovery crawler.
5. A test that needs a cloud API key or a downloaded NER checkpoint stays opt-in. Pull-request CI stays offline.
6. Update this file's progress line when an item lands.

## Current facts the work attaches to

| Fact | Where |
|---|---|
| Regex-only baseline, package version string `0.17.0` | `tests/eval/baselines/gold_corpus_regex_only.json` |
| Public table with empty NER and LLM rows | `scripts/eval_public_table.py`, `tests/eval/baselines/public_eval_table.md` |
| Gold scorer (mention vs entity, direct vs quasi, leftover) | `tests/eval/gold.py`, `scripts/run_gold_benchmark.py` |
| NER is optional, model `urchade/gliner_small-v2.1`, labels person / organization / location / address / date | `span_ner.py`. There is no `--ner-model` flag. |
| Careful prompt asks for identity clues. Speed and cost profiles skip the language model when the `[ner]` extra is installed. | `prompts/detailed.py`, `conf.py` |
| Task calls and detection calls share `llm_provider.py` (`call(prompt, model_name)`). Detection prompts are not a user task. | `llm_provider.py` |
| HTTP is text-only, 5,000,000 characters, no authentication. `/health` reports the hardcoded version `0.26.0` while core is `0.31.0`. | `packages/pdf-anonymizer-api/src/pdf_anonymizer_api/app.py` |
| Date `shift` uses a different offset per value, derived from `base_form`. Intervals between two dates are not preserved. | `operators.py` `shift_date_value` |
| HIPAA profile sets year-only dates, ZIP3, and age 90+. | `EntityProfile.HIPAA_SAFE_HARBOR` in `conf.py` |
| OCR language is fixed at `eng`. An empty scan is already a hard error. | `pdf_ocr.py` |
| PDF input writes Markdown. `--output-pdf` adds a sanitized PDF. `--redact` is irreversible and stays opt-in. | `cli.py` |

---

### 1. Publish NER and careful-LLM scores

**Status:** not started

**Why:** The regex-only F1 of 0.26 is the number a reader can cite, and it measures the mode that misses names. A hospital or a law firm will ask for the other rows. The real-life careful path is a local Ollama model. One closed model is the ceiling on the same documents.

**Models (decided 2026-10-22)**

Score four rows. Do not score `gemini-2.5-pro`, which is still the `best-quality` default in `conf.py`. New Gemini API projects are being told that the 2.5 ids return 404. A consumer chat subscription cannot drive `run_gold_benchmark.py`. Google AI Plus ($4.99, the cheapest paid Gemini plan) and a Grok or X subscription are app quotas. The script needs an API key. Free-tier Gemini is marked "used to improve our products"; the paid API tier is marked not. Run closed models on a billed key.

| Row | Model id the script records | Role |
|---|---|---|
| `regex-only` | none | Floor. Offline. Already the CI gate. |
| `ner` | `urchade/gliner_small-v2.1` | Fast local detector. No language model. |
| `local-detailed` | `ollama/gemma4:12b-it-qat` | Careful local path. RE2 plus the detailed prompt. Approved 2026-10-22. |
| `closed-detailed` | `google/gemini-3.8-flash` | Full corpus, paid Gemini API. Detailed prompt. |

`gemma4:12b-it-qat` is the local model. It is an 11.9B quantization-aware 4-bit build, about 7.2 GB. The scoring machine is an RTX A2000 with 8 GB, so a 27B Q4 file does not stay on the GPU. The run sets `num_ctx` 8192, thinking off, and temperature 0. Ollama on this machine must be new enough to load Gemma 4 (0.30 or later). The row is RE2 plus the detailed prompt. It does not include GLiNER. `phi4-mini` stays the README example and is not this row.

`gemini-3.8-flash` is the closed model for the full 6,761 documents. It is the current Flash id, introductory API price $0.75 / $3.75 per million input / output tokens through 31 December 2026, then $1.50 / $7.50. Gemini 3.5 Flash-Lite is cheaper ($0.30 / $2.50) and is the wrong model for identity clues. Gemini 4 Argon and Gemini 3.1 Pro are stronger and several times the output cost. Google AI Plus does not include them. They stay off the full run.

A good Grok subscription (SuperGrok at $30, or the newer X Premium / Super / Ultra plans) does not include API tokens. The xAI API is a separate bill: grok-4.3 is about $1.25 / $2.50 per million, grok-4.7 is about $2 / $6, and 4.7's context is 500k rather than 1M. This repo has no xAI provider (`ModelProvider` is Google, Ollama, Hugging Face, OpenRouter, OpenAI, Anthropic). Do not block item 1 on a new provider. Optional later, on a fixed sample (TAB test, the domain pack, and 200 Gretel docs): `grok-4.3` with reasoning off, via OpenRouter or a small xAI adapter. Use grok-4.7 only on that sample if the 4.3 row is already in hand. Heavy / multi-agent mode is the wrong tool for a span list.

Record token counts and parse-failure counts in each baseline. A local model that returns prose instead of JSON looks like a missed name. One full Flash pass is on the order of tens of dollars if the average document is a few thousand tokens. TAB judgments are longer. The sample is how we compare Argon or grok-4.3 without paying that length six thousand times.

**Do**

- Teach `scripts/run_gold_benchmark.py` a `--profile regex-only|ner|local-detailed|closed-detailed` switch. `regex-only` stays the default and stays offline.
- `ner` calls `extract_entities_via_ner` on each gold document, then the same `evaluate_documents` and `leftover_report` path. Skip with a clear message when the `[ner]` extra or the checkpoint is absent. Do not download a model inside pull-request CI.
- Write `tests/eval/baselines/gold_corpus_ner.json` only from an explicit `--write-baseline` on a machine that has the model. Record package version, model id, document count, and the corpus manifest hashes that `gold_corpus_regex_only.json` already records.
- `local-detailed` runs RE2 plus the detailed prompt through `ollama/gemma4:12b-it-qat`, with `num_ctx` 8192, thinking off, and temperature 0. It writes `tests/eval/baselines/gold_corpus_local_detailed.json`. Pull-request CI must not pull the weights.
- `closed-detailed` calls the detailed prompt through `google/gemini-3.8-flash` on a billed `GOOGLE_API_KEY`. It writes `tests/eval/baselines/gold_corpus_closed_detailed.json`. Pull-request CI must not call it. Pass `--model-name` so a later sample run can target `grok` without a second script.
- Change `scripts/eval_public_table.py` so a row is filled when its baseline file exists, and the placeholder text no longer says item 20 is unshipped. Mention precision, recall, F1, leftover, and structured leftover stay the columns. Add entity F1 beside mention F1. The scorer already computes it.
- Re-run regex-only on the current tree and replace the 0.17.0 baseline in the same pull request, so the rows are comparable.
- Update `docs/project/gold-corpus.md` so it matches the script. Name the model id next to each row. Keep the sentence that this is not a legal privacy proof.
- Add a direct-versus-quasi split to the printed table. TAB-style scoring already has the split. Hiding it makes a high structured-identifier score look like a high name score.

**Do not**

- Do not put the NER or LLM numbers on the root `README.md` in this pull request. The gold-corpus page is the place.
- Do not lower the existing CI gate (structured mention recall 1.0 and structured leftover 0 on mini-tab plus the domain pack).
- Do not fail CI when the large downloaded corpus is absent.

**Done when:** `make gold-table` prints a NER row from a committed file, or an explicit "not measured on this machine" line. The checked-in table has a real NER row, a `local-detailed` row for `ollama/gemma4:12b-it-qat`, and a `closed-detailed` row for the approved closed model, each with its model id. A missing opt-in run stays a line that says it was not run. The regex row's `package_version` matches `pdf-anonymizer-core`.

**Touches:** `scripts/run_gold_benchmark.py`, `scripts/eval_public_table.py`, `tests/eval/baselines/`, `docs/project/gold-corpus.md`, a unit test that the table renderer fills a row from a tiny fixture.

**Prerequisite:** none.

---

### 2. One local round-trip command

**Status:** not started

**Why:** The useful industry loop is mask, ask an outside model to summarize or translate, then restore. Recipes make the user run three commands and remember not to attach the mapping file. Limina, Skyflow, and Philter sell that loop as a gateway. The engine already has both halves.

**Do**

- Add `pdf-anonymizer relay FILE --task-model MODEL --task "Summarize the document."`
- Run the existing anonymize path on the file. Hold the mapping in memory. Do not write `*.mapping.json` unless the user passes `--save-mapping`.
- Build a task prompt from the anonymized text only. Call `llm_provider` with `--task-model`. Detection may use another model via the existing `--model-name`. Require `--task-model` on the command line so a cloud call cannot be implicit.
- Deanonymize the model reply with the in-memory map. Write the restored text under `data/deanonymized/`.
- Refuse to start the task call if the outbound prompt contains any original value from the map or any mapping JSON.
- On task-call failure, write nothing that contains original values, and return a non-zero exit.

**Do not**

- Do not change `run` or `deanonymize`.
- Do not send the mapping file, the entity list, or the source path to the task model.
- Do not cache the task prompt in `data/cache/llm_responses.json` when that cache would store the anonymized document by default. Disable the cache for `relay` unless the user passes the existing cache flag on purpose. Check the cache key path before merging.
- Do not build an HTTP proxy in this pull request. That is item 7.

**Done when:** A test double records the outbound prompt and the restored reply. The prompt contains `PERSON_1` and does not contain the fixture's original name. The restored file contains the original name. A second test deletes the task-model response and asserts that no mapping file was created.

**Touches:** `cli.py`, a small helper next to `llm_provider.py` (prompt assembly only), `tests/test_relay.py`, one recipe on `docs/project/recipes.md`.

**Prerequisite:** none. Advertise it only after item 1 has a NER or LLM leftover number, so the recipe can point at that page.

---

### 3. Security review of the local service

**Status:** not started
**Absorbs:** improvement-plan item 27.

**Why:** `POST /deanonymize` turns stand-ins back into names and has no authentication. A hospital or a bank stops a pilot there. The tool also does not say, in the README, that it does not ship logs off the machine. `/health` reports version `0.26.0` while the package is `0.31.0`.

**Do**

- If `ANONYMIZER_API_TOKEN` is set, require `Authorization: Bearer` on every route except `GET /health`. Compare with `hmac.compare_digest`. A missing or wrong token is HTTP 401 and an empty body.
- If `--host` is not a loopback address, refuse to start when the token is unset.
- Loopback with no token keeps today's open behavior, and the process logs one warning at startup. That preserves current `curl` recipes on `127.0.0.1`.
- Append one JSON line per deanonymize, from the CLI and from HTTP, to `data/stats/audit.log` (mode `0600`). Fields: time, command (`cli` or `http`), restored count, whether a mapping file path was used. Do not write original values, placeholder values, or document text.
- Add a short no-telemetry paragraph to the root README and to `docs/project/http-service.md`: the process does not send usage data; a cloud model runs only when the user selects one; the audit file stays on disk.
- Read the API version from installed package metadata. Delete the hardcoded `0.26.0`.
- In the release workflow, publish SHA-256 checksums for the wheels. Sigstore attestations are welcome if the existing GitHub workflow can do them without a new vendor. Checksums alone close item 27.

**Do not**

- Do not add an account system, SSO, or a remote log sink.
- Do not log prompts.
- Do not require a token on loopback in this pull request. Item 4's review page is the exception: that page must not start without a token.

**Done when:** `tests/test_http_api.py` covers 401, loopback-open, and non-loopback refusal. An audit test asserts the log line has no fixture name in it. README contains the no-telemetry paragraph. `GET /health` returns the core or API package version from metadata.

**Touches:** `app.py`, `cli.py` deanonymize path, `.github/workflows/`, README, `docs/project/http-service.md`, `docs/project/mapping-security.md`.

**Prerequisite:** none. Item 4 depends on this.

---

### 4. Local review desk

**Status:** not started

**Why:** Legal bundles, clinical release, and subject-access packs stop until a person accepts or skips each span. `pdf-anonymizer apply` rewrites from a report. It does not show the span, the score, or the source (`regex`, `ner`, `llm`, `deny-list`).

**Do**

- Add `pdf-anonymizer review FILE`. It runs detection, writes no anonymized output yet, and starts the existing API on `127.0.0.1` with a fresh token printed once in the terminal.
- Serve one HTML page from the API package. No frontend build, no extra framework. The page lists each entity: text, type, score, source, and the stand-in it would become. Buttons: accept, skip. A final action writes the file through the existing replace path, honoring operators.
- Decisions are a JSON list of `{start, end, type, accept}`. `POST` that list back to the local process. Reject a decision whose offsets do not match the session.
- Default decisions are accept for score at or above `--min-confidence`, skip below it. The page starts from those defaults.
- Bind only loopback. Refuse to start if the token from item 3 is missing. The command generates one when the environment variable is unset.
- PDF and Word inputs use the writers that already exist. Skipping a span leaves the original characters in the output. Say that on the page.
- Shut the server down when the user saves or presses Ctrl-C. Do not keep the cleartext session on disk. A temp file, if any, is mode `0600` and removed on exit.

**Do not**

- Do not change `run` to open a browser.
- Do not auto-apply residual reports. `apply` stays a separate command.
- Do not send page contents to a CDN or a font host. The page is one file of HTML.

**Done when:** A test client accepts one span and skips one span on a fixture string, and the output contains the stand-in and the skipped original. A test hits the page port without the bearer token and gets 401.

**Touches:** new `review.html` and routes in `pdf-anonymizer-api`, a session object in core (entities plus decisions, no I/O), `cli.py`, `tests/test_http_api.py`, a recipe.

**Prerequisite:** item 3's bearer check.

---

### 5. Clinical and legal profiles

**Status:** not started

**Why:** Buyers do not test "entity count". They test a discharge note and a retainer. The HIPAA profile is a coverage aid for the 18 Safe Harbor classes. It is the wrong default for a note whose dates must keep their intervals, and the wrong default for a pleading whose firm name must stay visible.

**Do**

- Add `EntityProfile.CLINICAL_AID` (`clinical-aid`) and `EntityProfile.LEGAL_AID` (`legal-aid`) next to `hipaa-safe-harbor` in `conf.py`.
- `clinical-aid` includes the current HIPAA type list plus `MEDICAL_RECORD` and facility names as `ORGANIZATION`. Ages of 90 and over still generalize. Document the profile as an aid, with the same force as the HIPAA sentence.
- Add a document-level date shift. One integer offset per file, derived from `--date-shift-secret` or a generated secret stored only in the mapping file. Every date in that file moves by that same number of days. Today's `shift_date_value` stays as it is for callers who pass the per-value operator. The profile uses the document-level offset. Intervals between dates in one file stay equal.
- `legal-aid` hides person, address, email, phone, and case-number-like ids. It does not hide a phrase listed in `--keep-list`. Ship `entities.example.txt` additions or a small `legal-keep.example.txt` that shows a firm keeping its own name. Do not hard-code a firm.
- Extend `tests/eval/domain_pack.json` with a handful of synthetic clinical notes and synthetic pleadings. English first. No real patient or client text. Include one identity clue in each set ("the only in-house counsel at Northwind Clinics").
- Score those pages with item 1's harness. The pull-request gate for this item is the committed domain pack under regex-only: structured mention recall stays 1.0 on the new structured spans (MRN, email, phone, case id). Name recall is reported when NER is available and is not a CI failure in the extra-less install.

**Do not**

- Do not rename or retune `hipaa-safe-harbor`.
- Do not say the profile meets HIPAA, GDPR, or a court rule.
- Do not run *k*-anonymity on these documents. Tables keep `--k`.

**Done when:** `pdf-anonymizer run note.txt --entity-profile clinical-aid` shifts both dates in a fixture by the same number of days, generalizes an age of 95, and hides the MRN. `legal-aid` hides the client and keeps the firm name that is on the keep-list. Domain-pack CI still passes.

**Touches:** `conf.py`, `operators.py` (document-level shift only), CLI `--entity-profile` choices, `tests/eval/domain_pack.json`, `tests/test_entity_profile.py`, recipes.

**Prerequisite:** item 1's scorer, so the new pages are not scored by a one-off script.

---

### 6. Documents people actually have

**Status:** not started
**Two pull requests.** 6a then 6b.

#### 6a. OCR language and unreadable pages

**Why:** National-id patterns already cover Germany, France, and Spain. Free text in those languages, and scanned pages, are what the files look like. OCR always asks Tesseract for `eng`. A stamp, a photo of an identity card, or handwriting can still leave a page blank after OCR, and the run can look successful if some other page had text.

**Do**

- Add `--ocr-lang` (default `eng`). Pass it to `ocr_pdf`. A missing Tesseract language pack is an error that names the pack, not an empty success.
- Add `--ner-model` (default `urchade/gliner_small-v2.1`). Do not change the default checkpoint in this pull request. Document a multilingual checkpoint as an opt-in once item 1 has scored it on the new pages.
- Add a short synthetic German, French, and Spanish page to the domain pack: a person name, an email, and one national id that `id-extract` already detects. The regex gate covers the id and the email. The name is scored when NER runs.
- Add one sentence to `prompts/detailed.py`: the document may not be English; hide names and identity clues in the language of the text. Leave `simple.py` alone.
- After OCR, record pages that still have no words. Write them into the existing stats JSON as `unreadable_pages` (page numbers only). If every page is unreadable, keep today's hard error.
- State in `docs/project/troubleshooting.md` that Tesseract does not reliably read handwriting or a photograph of an identity card.

**Do not**

- Do not add a second OCR engine.
- Do not make `--ocr` the default. A digital PDF must not pay for Tesseract.
- Do not treat the three new pages as a translation of the whole product UI.

#### 6b. Sanitized PDF beside Markdown

**Why:** The file the user opened is a PDF. Markdown remains the right input to a model. The file they send to a person should be the sanitized PDF that `--output-pdf` already writes.

**Do**

- When the input suffix is `.pdf`, write the sanitized PDF as well as Markdown, unless the user passes `--no-output-pdf`.
- Leave `--redact` off unless the user asks. Redaction cannot be deanonymized.
- Update tests that list output files. The changelog sentence says Markdown is still written.
- Keep non-PDF inputs on their current writers (Word stays Word, CSV stays CSV).

**Do not**

- Do not stop writing `*.anonymized.md` for PDF inputs.
- Do not wipe Markdown sidecars of their text. Metadata wipe stays on the PDF path, where it already exists.

**Done when:** A PDF fixture produces both outputs by default, `--no-output-pdf` produces only Markdown, and a scan with `--ocr-lang eng` either yields words or a named error. The domain pack contains one page each for German, French, and Spanish, and the structured-id gate passes.

**Touches:** `pdf_ocr.py`, `load_and_extract.py`, `cli.py`, `span_ner.py`, `prompts/detailed.py`, `tests/eval/domain_pack.json`, `docs/project/troubleshooting.md`, `docs/project/cli-usage.md`.

**Prerequisite:** none for the code. Land 6a before 6b so the default PDF is not the only change in a redaction review.

---

### 7. OpenAI-compatible proxy (deferred)

**Status:** deferred

**Why:** Item 2 is the same privacy property for a file the user already has. A proxy is the same property for an application that already calls `https://api.openai.com/v1/chat/completions`. It is a larger attack surface (streaming, tool calls, retries, the token from item 3).

**Do, later**

- Listen on loopback only, require the item 3 token, accept a chat-completions body, mask message content, forward stand-in text to the upstream the user named, restore the completion, and apply the item 2 test: originals never leave the process.
- Support one non-streaming chat completion first. Streaming and tool arguments wait.

**Do not start this until** items 2 and 3 have merged and a recipe shows `relay` in use.

---

## Out of scope

| Idea | Why it is not in this plan |
|---|---|
| Tor, a live USB, Qubes, VPN routing | Different threat model. `docs/temp/deep-research-report (7).md` is wrong to treat those as product features. |
| Replace GLiNER or the careful prompt with a clinical model the size of John Snow Labs | A different product and a different license. Item 1 tells us how far the current stack is. A model swap is a later decision with those numbers. |
| NIST FF3 format-preserving encryption, KMS, HSM | `encrypt` is already an AES-256-GCM token. A format-preserving mode is a separate operator. It is not required for the six jobs above. |
| *k*-anonymity, ℓ-diversity, or differential privacy on prose | Item 26 already covers optional *k* on CSV and Excel. Do not extend it to PDFs. |
| Audio, video, faces, logos | Another product. Item 6 records unreadable pages instead of pretending OCR saw them. |
| Org-wide bucket discovery | A DLP crawler. |
| A compliance certificate | HHS does not certify this kind of tool. Profiles stay aids. |
| Authentication accounts and SSO | A bearer token and a local audit line are the security review this service needs. |

## Definition of done (each item)

- Tests cover the new behavior and the unchanged default of `run`, except the PDF extra file in item 6b.
- `uv run ruff check .` and `uv run pytest` pass.
- User-facing text goes in recipes, CLI help, or the gold-corpus page. The root README gains only the no-telemetry paragraph in item 3.
- This file's progress checkbox is updated when the item merges.
- Pull-request CI does not gain an API key, a model download, or a network call.
