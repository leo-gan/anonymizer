# Internal improvement plan

**Status:** living plan  
**Audience:** maintainers only  
**Do not publish.** This directory is excluded from the MkDocs / GitHub Pages build (`exclude_docs` in `mkdocs.yml`). Do not link it from `README.md`, `docs/index.md`, or the public nav.

## Progress

- [x] 1. Prompt: implied / contextual PII — done 2026-08-14, [PR #40](https://github.com/leo-gan/anonymizer/pull/40)
- [x] 2. Checksum validators on structured regex hits — done 2026-08-14, [PR #41](https://github.com/leo-gan/anonymizer/pull/41)
- [x] 3. Country filter for regex patterns — done 2026-08-14, [PR #42](https://github.com/leo-gan/anonymizer/pull/42)
- [x] 4. Residual-PII verification pass — done 2026-08-14, [PR #43](https://github.com/leo-gan/anonymizer/pull/43)
- [x] 5. Encrypted mapping file — done 2026-08-15, [PR #44](https://github.com/leo-gan/anonymizer/pull/44)
- [x] 6. Generalization and per-entity operators — done 2026-08-15, [PR #45](https://github.com/leo-gan/anonymizer/pull/45)
- [x] 7. Quasi-identifier / linkage risk report — done 2026-08-15, [PR #46](https://github.com/leo-gan/anonymizer/pull/46)
- [x] 8. HIPAA Safe Harbor entity profile — done 2026-08-15, [PR #47](https://github.com/leo-gan/anonymizer/pull/47)
- [x] 9. Format-preserving synthetic replacements — done 2026-08-15, [PR #48](https://github.com/leo-gan/anonymizer/pull/48)
- [x] 10. Cross-document consistent placeholders — done 2026-08-15, [PR #49](https://github.com/leo-gan/anonymizer/pull/49)
- [x] 11. Allowlist / denylist gazetteers — done 2026-08-15, [PR #50](https://github.com/leo-gan/anonymizer/pull/50)
- [x] 12. Span-based replacement — done 2026-08-15, [PR #51](https://github.com/leo-gan/anonymizer/pull/51)
- [x] 13. TAB-style eval harness — done 2026-08-15, [PR #52](https://github.com/leo-gan/anonymizer/pull/52)
- [x] 14. OCR for scanned PDFs — done 2026-09-04, [PR #62](https://github.com/leo-gan/anonymizer/pull/62)
- [ ] 15. In-place PDF redaction (vector rewrite + metadata sanitization)
- [x] 16. Regex-only / offline mode — done 2026-08-15, [PR #55](https://github.com/leo-gan/anonymizer/pull/55)
- [x] 17. Secure mapping encryption workflow (Argon2id, AAD, 0600, ephemeral, wipe) — done 2026-08-15, [PR #54](https://github.com/leo-gan/anonymizer/pull/54)
- [x] 18. CSV / Excel as an input format (cell-level PII masking) — done 2026-08-19, [PR #56](https://github.com/leo-gan/anonymizer/pull/56) / [PR #57](https://github.com/leo-gan/anonymizer/pull/57) / [PR #58](https://github.com/leo-gan/anonymizer/pull/58)
- [x] 19. Completeness testing (gold E2E, CI coverage, fuzz, leftover red-team) — done 2026-09-03, [PR #60](https://github.com/leo-gan/anonymizer/pull/60)
- [ ] 20. Local span NER (GLiNER-class) as `best-speed`
- [ ] 21. Per-span confidence and recognizer provenance
- [ ] 22. HTTP API + Docker
- [ ] 23. Review / apply residual findings
- [ ] 24. `encrypt` / format-preserving encryption operator
- [x] 25. Native DOCX input/output — done 2026-09-04, [PR #61](https://github.com/leo-gan/anonymizer/pull/61)
- [ ] 26. Optional table-only formal privacy engine
- [ ] 27. Release hygiene (attestations, no-telemetry statement)

---

## Purpose

Ship the next privacy upgrades as **independent, reviewable changes**, in the order below. Each item can merge without waiting on the others. The sequence is value-first, not a hard dependency graph.

This plan is grounded in `docs/101/history.md` (Anonymization Techniques and Breakthroughs), the current hybrid RE2 + LLM pipeline (`packages/pdf-anonymizer-core`), and the 2026 SOTA comparison in [`sota-research.md`](sota-research.md) (session research + `docs/temp/` reports). New items 19–27 are that comparison, turned into one-PR work. Item 19 (completeness testing) is a first-class feature, not a process footnote: leftover rate and recall are how this product proves it is best in class.

---

## Current position

This product is a **reversible document pseudonymizer**: typed placeholders (`PERSON_1`, `EMAIL_3.v_1`) plus a JSON mapping file. It is not a statistical anonymizer.

| Technique (history.md) | Today |
|---|---|
| Data removal / identifier stripping | Hybrid RE2 + LLM NER, then span-based replacement |
| Pseudonymization | Typed tokens + `data/mappings/*.json` (optional AES-256-GCM + Argon2id; or in-memory only) |
| Generalization / suppression | Operators: `mask`, `hash`, `generalize`, `shift` (default still `replace`) |
| Randomization / differential privacy | Not implemented (poor fit for reversible prose) |
| *k*-anonymity / ℓ-diversity / *t*-closeness | Not implemented (tabular models; do not rewrite PDFs with them) |
| Synthetic data | Value-level `fake` operator (seeded Faker); not whole-document rewrite |
| Cryptographic methods | Optional AES-256-GCM + Argon2id mapping (`*.mapping.json.enc`), source-file AAD, `0600` writes |
| Re-ID / attack simulation | Residual regex scan + linkage-risk report + TAB-style eval harness (`tests/eval/`). Downloadable gold-corpus (TAB, Presidio, Gretel) + regex-only baseline. CI leftover/recall gate, residual JSON red-team, coverage floor, Hypothesis fuzz, public eval table (item 19). |

Known code facts to attach to:

- `conf.py`: regexes are still structural. After a match, `validators.py` runs a cheap check (Luhn, IBAN, VIN, a few national IDs). Failures stay hidden as `TYPE_LIKE` (`IBAN_LIKE_1`).
- `core.py`: replacement is span-based (locate in `full_text`, longest-first, write from the end). Shipped in [PR #51](https://github.com/leo-gan/anonymizer/pull/51).
- `prompts/detailed.py`: asks for identity clues (`INDIRECT`, or `PERSON` with a known `base_form`) plus birthdates; `simple.py` does not. Shipped in [PR #40](https://github.com/leo-gan/anonymizer/pull/40).
- Mapping files are plaintext by default. `--mapping-passphrase` / `ANONYMIZER_MAPPING_KEY` writes `*.mapping.json.enc` (AES-256-GCM + Argon2id, source SHA-256 AAD, atomic `0600`). `--ephemeral-mapping` never writes the map.
- `--operator TYPE=mask|hash|generalize|shift|fake` changes how a type is written. Default remains `replace` (PERSON_1).
- `--entity-profile hipaa-safe-harbor` is a coverage aid (year-only dates, ZIP3, age 90+). Not a compliance certificate.
- National-ID regexes can be limited with `filter_regex_patterns(["US", "GB"])` or CLI `--countries US,GB`. Universal patterns always stay.
- `--no-llm` / `-p regex-only` skips the language model. Regex, checksums, operators, verify, and risk still run. Names and identity clues are missed.
- `--keep-list` / `--deny-list` gazetteers. Keep wins if a phrase is on both lists.
- `tests/eval/` scores mention-level and entity-level recall, split by direct vs quasi identifiers. `scripts/eval_tab.py` runs the fixture (regex stage if no predictions file). `scripts/download_gold_corpus.py` installs TAB / Presidio / Gretel into `data/gold-corpus/` (not in git). Regex-only baseline: `tests/eval/baselines/gold_corpus_regex_only.json`. PR CI: committed gold leftover/recall gate, residual JSON red-team, `pytest-cov` floor, Hypothesis fuzz. Public eval table: `scripts/eval_public_table.py`. LLM path in unit tests is mocked; live LLM eval is opt-in.
- `.csv` / `.xlsx` take a table path (`tables.py`): per-cell regex on text/formula strings, row-addressed LLM batches, per-cell apply. Still pseudonymization, not *k*-anonymity (item 18).
- `.docx` takes a Word path (`word.py`): per-paragraph regex on visible text (runs joined), part-wise LLM flatten, per-paragraph apply, native `.docx` write-back. Headers, footers, comments, field codes, and hyperlink targets are walked. `.doc` / `.docm` / `.dot*` are rejected (item 25).
- PDF path is `pymupdf4llm` → Markdown. A PDF with pages and no text layer is a hard error unless `--ocr` (Tesseract on PATH) recovers words. OCR writes `*.anonymized.layout.json` boxes for a later native-PDF redact (item 14). `--output-pdf` writes a sanitized native PDF (PyMuPDF redaction annotations + ``apply_redactions``, ``/Info``/XMP/attachments/layers wiped). `--redact` is irreversible black boxes. Markdown stays the default (item 15).
- `best-speed` still calls an LLM for names. No GLiNER/spaCy span stage, no per-span confidence (items 20–21).
- Surface is CLI + SDK. No HTTP service, no Docker image (item 22). Residual/risk reports do not rewrite (item 23).

---

## Working rules

1. **One item, one PR** unless two items are trivial and naturally share a file.
2. **Default behavior stays the same** unless the item is a prompt-only quality fix. New capabilities are flags, profiles, or post-steps.
3. **Do not claim legal compliance.** HIPAA / GDPR wording is “aid”, not certification.
4. **Do not implement** *k*-anonymity / ℓ-diversity / *t*-closeness as document rewriters, differential privacy on prose, mixnets, HME/MPC, or whole-document GAN rewrites. See [Out of scope](#out-of-scope).

---

## Ordered work

### 1. Prompt: implied / contextual PII

**Status:** done (2026-08-14) — [PR #40](https://github.com/leo-gan/anonymizer/pull/40) (`feat/implied-contextual-pii`)

**Technique:** data removal beyond named entities (Weld / Netflix lesson applied to prose).  
**Why first:** hours of work, no API break, highest ROI per line. `how-different.md` claims we catch “CEO of Tesla”; the detailed prompt does not ask for that.

**Do**

- Extend `packages/pdf-anonymizer-core/src/pdf_anonymizer_core/prompts/detailed.py`.
- Instruct the model to emit uniquely identifying descriptions (`INDIRECT`, or `PERSON` with a `base_form` when the implied person is known).
- Add 2–3 few-shot examples (job + org + city; “author of …”; unique role at a named company).
- Leave `simple.py` unchanged so `best-speed` / `best-cost` stay cheap.

**Touches:** `prompts/detailed.py`, `core.py` (`INDIRECT` type priority), mocked-LLM tests, 101 / recipes / README.  
**Prerequisite:** none.

---

### 2. Checksum validators on structured regex hits

**Status:** done (2026-08-14) — [PR #41](https://github.com/leo-gan/anonymizer/pull/41) (`feat/regex-checksum-validators`)

**Technique:** data removal with higher precision, without leaving mistyped numbers in the clear.  
**Why:** `DEFAULT_REGEX_PATTERNS` is over-inclusive (`CREDIT_CARD`, `IBAN`, `MEDICAL_NPI_US`, many national IDs). Shape-only hits used to become tokens or, if dropped, stay visible.

**Do**

- Add `validators.py` with Luhn (cards, NPI, Canadian SIN), IBAN mod-97 + country length, VIN check digit, and a few national-ID checksums.
- After `extract_entities_via_regex`, **do not drop** checksum failures. Relabel them `TYPE_LIKE` (`IBAN_LIKE_1`). Verified hits stay `IBAN_1`.
- Listing `IBAN` in `--anonymized-entities` also includes `IBAN_LIKE`.
- Keep regex patterns themselves unchanged.

**Touches:** `validators.py`, `regex_ner.py`, `core.py` (priority + type filter), tests, recipes / README.  
**Prerequisite:** none.

---

### 3. Country filter for regex patterns

**Status:** done (2026-08-14) — [PR #42](https://github.com/leo-gan/anonymizer/pull/42) (`feat/regex-country-filter`)

**Technique:** data removal, less noise. Already designed in `conf.py` comments, not exposed.

**Do**

- `filter_regex_patterns(countries=["US", "GB"])` (name as appropriate).
- Always keep universal keys: `EMAIL`, `PHONE`, `URL`, `CREDIT_CARD`, `IBAN`, `IPV4_ADDRESS`, `IPV6_ADDRESS`, `MAC_ADDRESS`, `CRYPTO_*`, `DATE_ISO`, etc.
- CLI: `--countries US,GB`.
- Document in recipes. Do **not** add a public 101 page for this.

**Touches:** `conf.py`, CLI, recipes.  
**Prerequisite:** none. Pairs well with (2) but must not wait on it.

---

### 4. Residual-PII verification pass

**Status:** done (2026-08-14) — [PR #43](https://github.com/leo-gan/anonymizer/pull/43) (`feat/residual-pii-verify`)

**Technique:** the “Attack Simulation” box in history.md; Ohm / Netflix / AOL.  
**Why:** there is no check that the *output* is clean. Chunked LLM + regex can both miss.

**Do**

- After replacement, re-run regex NER on the anonymized text (cheap, default on).
- Optionally a short LLM “find remaining PII” prompt behind `--verify-llm`.
- Write `data/stats/<stem>.residual_pii.json`.
- CLI: `--verify` / `--no-verify` and `pdf-anonymizer verify`.
- **Report first. Do not auto-rewrite.**

**Touches:** `verify.py`, CLI, recipes / README. `anonymize_file` return contract unchanged.  
**Prerequisite:** none.

---

### 5. Encrypted mapping file

**Status:** done (2026-08-15) — [PR #44](https://github.com/leo-gan/anonymizer/pull/44) (`feat/encrypted-mapping`)

**Technique:** cryptographic methods + GDPR “secure the key”.  
**Why:** with the map, output is pseudonymized personal data (WP29 / EDPB). A leaked `*.mapping.json` is a full deanonymization.

**Do**

- Optional `--mapping-passphrase` or `ANONYMIZER_MAPPING_KEY`.
- Write `mapping.json.enc` (AES-GCM, or age/nacl — pick one and stick to it).
- `deanonymize` decrypts when a key is present.
- **Default remains plaintext** for backward compatibility.
- Document the threat model in recipes only (mapping is the key).

**Touches:** `utils.save_results`, `deanonymize_file`, CLI flags.  
**Prerequisite:** none.

---

### 6. Generalization and per-entity operators

**Status:** done (2026-08-15) — [PR #45](https://github.com/leo-gan/anonymizer/pull/45) (`feat/entity-operators`)

**Technique:** generalization (the mechanism behind *k*-anonymity and HIPAA Safe Harbor) plus Presidio/Philter-style operators.  
**Why:** one strategy (`PERSON_1`) is wrong for every type. Cards should be masked, dates year-only, ZIPs truncated, SSNs never left reversible in a released file if the user does not want that.

**Do, in one PR or two stacked PRs**

1. Operator registry: `type → operator`. Operators: `replace` (current default), `mask`, `hash`, `generalize`, optionally `fake` later.
2. Deterministic generalizers:
   - ISO date → year (`2019`)
   - US ZIP → first 3 digits or `021**`
   - age `47` → `40-49`; age `>89` → `90+`
   - optional HIPAA-style date shift (same offset per `base_form`)
3. CLI: `--operator PERSON=replace --operator CREDIT_CARD=mask --operator DATE=generalize`.
4. Default remains `replace` for every type.

**Touches:** new `operators.py` / `generalize.py`, `core.py` replacement loop, `conf.py` defaults, CLI, recipes.  
**Prerequisite:** none. Cleaner if span-based replacement (backlog) exists; do **not** block on it.

---

### 7. Quasi-identifier / linkage risk report

**Status:** done (2026-08-15) — [PR #46](https://github.com/leo-gan/anonymizer/pull/46) (`feat/linkage-risk-report`)

**Technique:** *k*-anonymity as a **diagnostic**, not a PDF rewriter. Sweeney, Dalenius, Netflix.

**Do**

- From the collected entity list, count co-occurring quasi-ID types per chunk or sliding window (`JOB_TITLE` + `ORGANIZATION` + `LOCATION`, unique person+city, etc.).
- Flag rare combinations.
- Emit `data/stats/<stem>.risk.json` with `high` / `medium` / `low` and evidence spans.
- **No text mutation.**

**Touches:** new `risk.py`, post-step after entity collection (or a CLI `report` command).  
**Prerequisite:** none. Quality jumps after (1) because implied identities become entities.

---

### 8. HIPAA Safe Harbor entity profile

**Status:** done (2026-08-15) — [PR #47](https://github.com/leo-gan/anonymizer/pull/47) (`feat/hipaa-entity-profile`)

**Technique:** legal standard from the same history chapter (HIPAA 2003, 18 identifiers).  
**Why:** `--anonymized-entities` is a raw type list. Health users need a named profile.

**Do**

- Add `EntityProfile.HIPAA_SAFE_HARBOR` (or equivalent), not a fourth speed/quality `ConfigProfile` unless that is clearly better.
- Require coverage of the 18 identifier classes that apply to text: names; geos smaller than state; dates (except year); phones; faxes; emails; SSNs; MRNs; health-plan IDs; accounts; license numbers; vehicle IDs; device IDs; URLs; IPs; biometrics / photos (flag only — we do not redact pixels yet).
- Wire generalization from (6): ZIP3, year-only dates, age `>89` → `90+`.
- Extend the detailed (or a dedicated) prompt to ask for those categories — not “birthdates only”.
- CLI: `--entity-profile hipaa-safe-harbor`.
- Docs must say: **aid, not a compliance certification.**

**Touches:** `conf.py`, prompts, CLI, recipes.  
**Prerequisite:** none. Much better after (1), (3), and (6). Can ship as type-coverage-only if (6) is not merged yet.

---

### 9. Format-preserving synthetic replacements

**Status:** done (2026-08-15) — [PR #48](https://github.com/leo-gan/anonymizer/pull/48) (`feat/fake-operator`)

**Technique:** synthetic data at *value* level, not whole-document GANs.  
**Why:** Downstream readers (and LLMs) reason better over `Jane Alvarez` than `PERSON_1`. Raw values stay in the local mapping.

**Do**

- Add operator `fake`.
- Seed with `hash(secret, base_form, type)` so the same person always gets the same fake.
- Optional `--fake-secret` / `ANONYMIZER_FAKE_SECRET`. Default secret is a built-in constant (stable, not private).
- Keep mapping original → fake so deanonymize still works.

**Touches:** `operators.py`, `core.py`, CLI, recipes.  
**Prerequisite:** none (builds on (6)).

---

### 10. Cross-document consistent placeholders

**Status:** done (2026-08-15) — [PR #49](https://github.com/leo-gan/anonymizer/pull/49) (`feat/cross-document-placeholders`)

**Technique:** pseudonymization for longitudinal studies.  
**Why:** Batch mode treats each file alone. `John Doe` is `PERSON_1` in file A and `PERSON_7` in file B.

**Do**

- `--mapping-in existing.mapping.json` seeds placeholder counts and `base_entity_placeholders`.
- Write an updated combined map.
- Works with encrypted maps when a passphrase is set.

**Touches:** `anonymize_file`, CLI.  
**Prerequisite:** none.

---

### 11. Allowlist / denylist gazetteers

**Status:** done (2026-08-15) — [PR #50](https://github.com/leo-gan/anonymizer/pull/50) (`feat/keep-deny-lists`)

**Technique:** foundational NER (deny-lists / keep-lists).  
**Why:** “Apple” the fruit vs “Apple Inc.”; your own org name should stay visible.

**Do**

- `--keep-list` / `--deny-list` files (one phrase per line).
- Keep-list skips replacement. Deny-list forces an entity even if regex/LLM missed it.

**Touches:** merge step in `core.py`, CLI.  
**Prerequisite:** none.

---

### 12. Span-based replacement

**Status:** done (2026-08-15) — [PR #51](https://github.com/leo-gan/anonymizer/pull/51) (`feat/span-replacement`)

**Technique:** engineering. Makes operators and generalization more correct.  
**Why:** Global string replace can change `May` inside the wrong word. Regex `finditer` offsets are thrown away today.

**Do**

- Carry `start`/`end` (per chunk, mapped back to `full_text`).
- Replace intervals, longest-first, no overlap.

**Touches:** `regex_ner.py`, `core.py`, optional LLM offsets.  
**Prerequisite:** none. Do not block other items on this.

---

### 13. TAB-style eval harness

**Status:** done (2026-08-15) — [PR #52](https://github.com/leo-gan/anonymizer/pull/52) (`feat/eval-harness`)

**Technique:** the open question in history.md: how do you measure leftover risk and utility?  
**Why:** Unit tests cover regex and mapping, not privacy metrics. No recall split for direct vs quasi identifiers.

**Do**

- `tests/eval/` or `scripts/eval_tab.py` on a small fixture (or TAB if licensed).
- Report mention-level and entity-level recall; split EMAIL/SSN vs LOCATION/DATE.
- Tests/scripts only. No product behavior change.

**Touches:** tests/scripts.  
**Prerequisite:** none.

---

### 14. OCR for scanned PDFs

**Status:** done (2026-09-04) — [PR #62](https://github.com/leo-gan/anonymizer/pull/62) (`feat/ocr-scanned-pdfs`)  
**Technique:** coverage.  
**Why:** Image-only PDFs yield empty text today (`pymupdf4llm` has nothing to read). SOTA (Presidio Image Redactor, Redactable, Azure scanned-PDF, Skyflow, Tonic Textual) OCR first. An empty extract that still writes `*.anonymized.md` is a silent compliance miss, not a hard error. See [`sota-research.md`](sota-research.md).

**Do**

- Optional OCR extra (e.g. Tesseract / ocrmypdf / PaddleOCR / Surya) behind a flag or extra.
- Map OCR boxes back to page coordinates so item 15 can redact the same spans.
- **Fail loudly** (non-zero exit, no “success” anonymized file) when a PDF/page has no extractable text and OCR is off or also empty.
- Document that this is a new dependency and a quality/speed trade.

**Touches:** `load_and_extract.py`, extras, CLI exit path, recipes.  
**Prerequisite:** none. Pairs with (15) and (19).

---

### 15. In-place PDF redaction (vector rewrite + metadata sanitization)

**Status:** not started  
**Technique:** different product surface; Adobe Sanitize / Redactable / Azure native-document class.  
**Why:** The product name implies a safe PDF. Markdown export drops layout, fonts, headers, and multi-column geometry. Overlay-only black boxes leave selectable text in `/Contents`. Hidden XMP, `/Info`, `/Prev` incremental-save history, attachments, layers, and annotations leak identity even when body text is masked. See [`sota-research.md`](sota-research.md).

**Do**

- Design first: PyMuPDF redaction annotations vs true content-stream rewrite (excise glyphs, drop orphan fonts). Rasterize-and-rebuild is the **scan fallback** (item 14), not the digital-PDF default.
- Keep Markdown export as default. Native PDF is opt-in (`--output-pdf`).
- Sanitize pass on every native-PDF write: XMP, `/Info`, `/Prev` history, attachments, hidden layers, annotations, thumbnails.
- Mapping must still round-trip if we claim reversibility. Irreversible “true redaction” is a second, explicit mode.
- Do not claim the output is legally de-identified.

**Touches:** new output path, CLI `--output-pdf`, recipes.  
**Prerequisite:** none. Large; design before coding. Quality of the redact path is measured by (19).

---

### 16. Regex-only / offline mode

**Status:** done (2026-08-15) — [PR #55](https://github.com/leo-gan/anonymizer/pull/55) (`feat/regex-only-offline-mode`)

**Technique:** data removal without a language model.  
**Why:** Air-gapped machines, cost, or structured logs where regex is enough.

**Do**

- `--no-llm` / profile that skips `identify_entities_with_llm`.
- Still run checksums, country filter, operators, verify, risk.
- Document that names and identity clues will be missed.

**Touches:** `core.py`, CLI, recipes.  
**Prerequisite:** none.

---

### 17. Secure mapping encryption workflow

**Status:** done (2026-08-15) — [PR #54](https://github.com/leo-gan/anonymizer/pull/54) (`feat/secure-encryption-workflow`, hardens item 5)

**Technique:** cryptographic methods + "secure the key", with a real threat model for local files.

**Why:** Item 5 shipped AES-256-GCM + scrypt. That stopped a casual leaked-file read, but left holes: no Argon2id, no document binding (AAD), umask `0644` mapping files, no atomic write, no metadata checks before KDF, no memory wipe / `mlock` / `MADV_DONTDUMP`, no ephemeral mode.

**Do**

- Keep writing AES-256-GCM. Switch KDF to Argon2id (still decrypt v1 scrypt envelopes).
- Bind source-document SHA-256 and schema version as GCM AAD.
- Validate envelope metadata before any KDF or decrypt. Constant-time compares for auth checks.
- Atomic `0600` writes (and `0700` mapping dir) for every mapping file, plaintext or encrypted.
- Wipe derived keys and plaintext PII buffers; `mlock` + `MADV_DONTDUMP` where supported.
- `--ephemeral-mapping`: never write `data/mappings/`.
- Tests that show the old holes and the fix (AAD tamper, permissions, wipe).
- Design note: `docs/project/mapping-security.md`.

**Touches:** `mapping_crypto.py`, `secure_memory.py`, `secure_io.py`, `utils.py`, CLI, tests, project docs.  
**Prerequisite:** none (rethink of item 5).

---

### 18. CSV / Excel as an input format (cell-level PII masking)

**Status:** done (2026-08-19) — [PR #56](https://github.com/leo-gan/anonymizer/pull/56) (CSV), [PR #57](https://github.com/leo-gan/anonymizer/pull/57) (Excel), [PR #58](https://github.com/leo-gan/anonymizer/pull/58) (docs / 0.17.0)

**Technique:** same reversible pseudonymization as PDF/MD/TXT, on table cells.  
**Why:** Users have rosters and exports. This is not k-anonymity.

**Do**

- Parse `.csv` (stdlib) and `.xlsx` (`openpyxl` extra) as tables.
- Per-cell regex on text/formula strings only; row-addressed LLM batches; per-cell `replace_entities` with the same entity-text key list as the text engine.
- Write `.anonymized.csv` / `.anonymized.xlsx` plus the existing mapping file.
- Deanonymize / verify / report on the same formats.
- Reject `.xls`, `.xlsm`, ODS. Drop Excel formulas (cached values only); neutralize CSV cells that start with `=` with a leading `'`; do not treat `+` / `@` as formulas.
- Do **not** implement k-anonymity / ℓ-diversity / t-closeness or a new store.

**Touches:** `tables.py`, `core.py` dispatch, `utils.save_results` / `deanonymize_file`,
CLI `verify`/`report`, extras, tests, recipes / CLI usage / architecture.  
**Prerequisite:** none.  
**Version:** 0.17.0 when user-facing.

---

### 19. Completeness testing (gold E2E, CI coverage, fuzz, leftover red-team)

**Status:** done (2026-09-03) — [PR #60](https://github.com/leo-gan/anonymizer/pull/60) (`feat/gold-corpus-benchmark`)  
**Priority:** important — measurement spine for remaining work; treat as a shipped feature, not a process footnote.

**Technique:** attack simulation / eval (history.md open question). Extends item 13 from “metrics helper + regex fixture” to a completeness gate. Grounded in the OS-report testing gap and [`sota-research.md`](sota-research.md) § gap 7.

**Why:** Unit tests and mocked LLM paths do not prove leftover risk. Competitors publish F1 / leak-rate. OCR, native PDF, and GLiNER cannot be claimed best-in-class if leftovers on a gold set never fail CI. Current state after this item: gold-corpus installer + regex-only baseline, CI leftover/recall gate on committed fixtures, residual JSON red-team, coverage floor, Hypothesis fuzz, public eval table. NER and live LLM columns wait on later items.

**Do**

1. **Gold-corpus system test.** Labeled synthetic fixture (expand `tests/eval/fixture.json`; TAB if licensed). Run `anonymize` end-to-end. Assert mention-level and entity-level recall (direct vs quasi) and a leftover-rate ceiling. Regex-only (and later NER) in PR CI. Live LLM is optional / nightly so PRs stay cheap and deterministic.
2. **Leftover red-team.** After anonymize, run the existing residual scan (`verify.py`) on the gold output. Fail the build if structured PII remains (emails, cards, IBANs, phones, IPs). Product already writes `*.residual_pii.json`; tests must use it as a gate.
3. **Coverage in CI.** `pytest-cov` on `pdf-anonymizer-core` / CLI. Publish the % on the PR. Pick a floor after the first baseline run; do not invent “90%” before measuring.
4. **Fuzz.** Hypothesis (or equivalent) on `regex_ner`, mapping envelopes (`mapping_crypto`), and PDF/table loaders. Malformed PDF bytes must not hang or write a “success” empty extract (pairs with item 14’s loud fail).
5. **Public eval table.** Script that prints regex-only vs NER (item 20) vs `detailed` LLM (nightly) on the gold set. Tests/scripts + CI artifact. No README marketing until numbers exist.

**Do not** require cloud API keys in PR CI. **Do not** auto-rewrite residuals here (that is item 23).

**Touches:** `tests/eval/`, `scripts/eval_tab.py`, `.github/workflows/ci.yml`, new fuzz tests, recipes (how to run the gold eval).  
**Prerequisite:** none. Item 13 is the starting point. Later detectors (20) and outputs (14, 15, 25) plug into the same gold set.

---

### 20. Local span NER (GLiNER-class) as `best-speed`

**Status:** not started  
**Technique:** three-tier detect: RE2 → local span model → LLM only for identity clues / low confidence. Philter Ph-Eye, Presidio spaCy, nvidia/gliner-PII, GLiNER2-PII.

**Why:** `best-speed` still calls an autoregressive model for names. That loses on cost, latency, and air-gap quality. LOGICAL (arXiv:2510.19346) and GLiNER2 SPY numbers are in [`sota-research.md`](sota-research.md). Keep `detailed` LLM for identity clues.

**Do**

- Optional extra (e.g. `[ner]`) with a GLiNER-class checkpoint. CPU-first.
- Wire as the semantic stage for `-p best-speed` / `best-cost`. `best-quality` still uses the LLM (and may use NER first).
- Default remains today’s LLM `best-speed` until the extra is installed **or** flip default only after item 19 shows NER ≥ current mocked-quality on the gold set.
- Names and orgs come from NER; identity clues stay LLM-only.

**Touches:** new detector module, `core.py` merge, `conf.py` profiles, extras, tests (19).  
**Prerequisite:** none. Much better after (21) so low-confidence spans can escalate to the LLM.

---

### 21. Per-span confidence and recognizer provenance

**Status:** not started  
**Technique:** Presidio-style 0–1 score + which recognizer fired.

**Why:** LLM JSON is uncalibrated. A threshold is how you trade recall vs over-redaction without editing prompts, and how item 20 gates the LLM.

**Do**

- Every entity object carries `score` (0–1) and `source` (`regex` / `ner` / `llm` / `deny-list`).
- CLI: `--min-confidence`. Default keeps today’s accept-all behavior.
- Regex checksums: verified hits score higher than `TYPE_LIKE`.
- Recipes only. No public “calibrated probability” claim.

**Touches:** `regex_ner.py`, LLM parse path, `core.py` merge, CLI, tests.  
**Prerequisite:** none.

---

### 22. HTTP API + Docker

**Status:** not started  
**Technique:** productization. Presidio and Philter are services.

**Why:** Pipelines and “drop in front of an LLM” expect `POST /anonymize` and `POST /deanonymize`. The OS-report sandbox point is valid for **untrusted PDFs**, not Tor.

**Do**

- Thin FastAPI on `pdf-anonymizer-core`: anonymize, deanonymize, verify, report.
- Official Dockerfile + compose. Optional AppArmor profile.
- No Spark/Ray/DuckDB UDFs in this item.
- Auth is out of scope (local bind / compose network).

**Touches:** new package or `packages/pdf-anonymizer-cli` extra, Dockerfile, recipes.  
**Prerequisite:** none.

---

### 23. Review / apply residual findings

**Status:** not started  
**Technique:** close the leftover loop. Report-only (item 4) stays the default.

**Why:** `*.residual_pii.json` and `*.risk.json` do not rewrite. Operators cannot accept a leftover email and apply it.

**Do**

- Opt-in apply: `--apply-residuals` or `pdf-anonymizer apply STATS_FILE`.
- Minimum viable: accept/skip list (JSON or TTY), then rewrite with the same span engine.
- HTML/TUI review can wait for a follow-up PR.
- Default remains report-only.

**Touches:** `verify.py`, `core.py` apply path, CLI, tests.  
**Prerequisite:** none (uses item 4 output).

---

### 24. `encrypt` / format-preserving encryption operator

**Status:** not started  
**Technique:** value-level crypto. Presidio encrypt/decrypt; Google AES-SIV / FPE-FFX; Philter FPE; NIST SP 800-38G AES-FF3-1.

**Why:** A leaked `mapping.json` (even `.enc` if the passphrase leaks) reverses every document. FPE keeps format and referential integrity without a central plaintext dictionary.

**Do**

- Operator `encrypt` (AES-GCM or similar; reversible with the mapping key).
- Optional `fpe` for digit-shaped types (cards, national IDs) via AES-FF3-1 if a maintained library is acceptable; otherwise ship `encrypt` first.
- Default remains `replace`.
- KMS/HSM envelope keys are a later hardening, not this PR.

**Touches:** `operators.py`, `core.py`, CLI, mapping-security note, tests.  
**Prerequisite:** none (builds on (6) and (17)).

---

### 25. Native DOCX input/output

**Status:** done (2026-09-04) — [PR #61](https://github.com/leo-gan/anonymizer/pull/61) (`feat/docx-input`)  
**Technique:** next document format. Azure Document PII and Philter Desktop already do Word.

**Why:** After native PDF, DOCX is the enterprise document users actually edit.

**Do**

- Read/write `.docx` without flattening to Markdown as the only output.
- Same hybrid detect + operators + mapping.
- Reject legacy `.doc` / macro-enabled formats (same spirit as item 18).
- HTML/JSON/EML are follow-ups, not this PR.

**Touches:** new loader/writer, CLI, extras, tests, recipes.  
**Prerequisite:** none.

---

### 26. Optional table-only formal privacy engine

**Status:** not started  
**Technique:** *k*-anonymity / ℓ-diversity / *t*-closeness / DP as a **table** engine (ARX class). Not a PDF rewriter.

**Why:** Cell-level CSV/XLSX (item 18) is still pseudonymization. Linkage on ZIP+gender+DOB is the actual tabular risk. Google SDP and ARX compute this; we only emit a prose linkage heuristic.

**Do**

- Separate path for `.csv` / `.xlsx` (later Parquet). Classify direct vs quasi IDs.
- Direct IDs: existing operators or item 24 FPE.
- Quasi IDs: opt-in generalization / suppression to a stated *k*. Report Prosecutor-style risk on the table. **No text mutation of PDFs.**
- Default remains today’s cell-level replace.
- Docs: aid, not a certificate.

**Touches:** `tables.py` or a sibling module, `report`, CLI flag, tests.  
**Prerequisite:** none. Do not block on (24).

---

### 27. Release hygiene (attestations, no-telemetry statement)

**Status:** not started  
**Technique:** trust in the supply chain. Filtered from the OS/network survey — not Tor, not a live USB.

**Why:** Open-source privacy tools are judged on “can I reproduce this wheel” and “does it phone home.” Code already has no telemetry; that is not written as a guarantee. CI does not publish checksums.

**Do**

- CI: publish wheel SHA-256 (and attestations if cheap).
- README / recipes: explicit no-telemetry, no-log-shipping statement; cloud LLM is opt-in and leaves the machine.
- Do not add analytics “just to check.”

**Touches:** `.github/workflows/`, README, recipes.  
**Prerequisite:** none.

---

## Out of scope

| Technique | Why not as a core feature |
|---|---|
| *k*-anonymity / ℓ-diversity / *t*-closeness as a **PDF** rewriter | Defined on tables of people, not narrative PDFs. Use (7) as a report. Cell-level CSV/Excel (18) is still pseudonymization. Optional table-only engine is item 26. |
| Differential privacy on the document | Calibrated noise destroys prose; ε is meaningless on one contract. Table-only DP may appear under (26), never on PDFs. |
| Mix / onion routing, Tor, I2P, VPN, live-USB OS, Qubes, browser fingerprinting | Communication / host anonymity. Different threat model. See [`sota-research.md`](sota-research.md). |
| Homomorphic encryption / MPC | Compute-on-encrypted-data; orthogonal to redaction. |
| Whole-document GAN / LLM synthetic rewrite | Memorization risk, unstable round-trip, fights reversibility. Prefer value-level fakes (9). |
| Audio / video redaction | Limina / Skyflow / CaseGuard class. Different product. |
| Org-wide S3/share discovery (Macie, Purview, Nightfall) | DLP crawler, not a document anonymizer. |
| HIPAA / SOC 2 **certificate** as a product claim | HHS does not certify products. Keep “aid, not a certificate.” |

---

## Independence (explicit)

Every numbered item can merge with **no prerequisite PR**. Soft couplings only:

- (9) `fake` is an operator on (6).
- (12) makes (6) and (9) more correct; do not block them on it.
- (10) is cleaner after (5) if the seed map is encrypted.
- (14) loud-fail + (15) native PDF are both scored by (19).
- (20) NER is the `best-speed` detector; (21) lets it escalate to the LLM; (19) is how we decide the default flip.
- (23) apply uses (4) report files.
- (24) `encrypt`/`fpe` is an operator on (6), hardened by (17).
- (26) is table-only; it must not rewrite PDFs.

Value-first order for **open** items (not a merge gate): **15** (native PDF) → **20** + **21** (local NER) → **22** (API) → **23** (apply) → **24** (FPE) → **26** (tables) → **27** (release).

---

## Definition of done (each item)

- Tests for the new behavior and for unchanged defaults.
- `uv run ruff check .` and `uv run pytest` pass.
- If user-facing: recipes (not 101) updated. No README marketing unless the feature is released and we choose to advertise it.
- This plan file updated (status / date) when an item lands.
