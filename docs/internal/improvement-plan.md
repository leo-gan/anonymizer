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
- [x] 11. Allowlist / denylist gazetteers — done 2026-08-15, `feat/keep-deny-lists`
- [ ] 12. Span-based replacement
- [ ] 13. TAB-style eval harness
- [ ] 14. OCR for scanned PDFs
- [ ] 15. In-place PDF redaction
- [ ] 16. Regex-only / offline mode

---

## Purpose

Ship the next privacy upgrades as **independent, reviewable changes**, in the order below. Each item can merge without waiting on the others. The sequence is value-first, not a hard dependency graph.

This plan is grounded in `docs/101/history.md` (Anonymization Techniques and Breakthroughs) and in the current hybrid RE2 + LLM pipeline (`packages/pdf-anonymizer-core`).

---

## Current position

This product is a **reversible document pseudonymizer**: typed placeholders (`PERSON_1`, `EMAIL_3.v_1`) plus a JSON mapping file. It is not a statistical anonymizer.

| Technique (history.md) | Today |
|---|---|
| Data removal / identifier stripping | Hybrid RE2 + LLM NER, then global string replace |
| Pseudonymization | Typed tokens + plaintext `data/mappings/*.json` |
| Generalization / suppression | Not implemented |
| Randomization / differential privacy | Not implemented (poor fit for reversible prose) |
| *k*-anonymity / ℓ-diversity / *t*-closeness | Not implemented (tabular models; do not rewrite PDFs with them) |
| Synthetic data | Not implemented |
| Cryptographic methods | Mapping stored as plaintext |
| Re-ID / attack simulation | Residual regex scan + linkage-risk report (`*.residual_pii.json`, `*.risk.json`) |

Known code facts to attach to:

- `conf.py`: regexes are still structural. After a match, `validators.py` runs a cheap check (Luhn, IBAN, VIN, a few national IDs). Failures stay hidden as `TYPE_LIKE` (`IBAN_LIKE_1`).
- `core.py`: replacement is whole-document string match, not character spans.
- `prompts/detailed.py`: asks for identity clues (`INDIRECT`, or `PERSON` with a known `base_form`) plus birthdates; `simple.py` does not. Shipped in [PR #40](https://github.com/leo-gan/anonymizer/pull/40).
- Mapping files are plaintext by default. `--mapping-passphrase` / `ANONYMIZER_MAPPING_KEY` writes `*.mapping.json.enc` (AES-256-GCM).
- `--operator TYPE=mask|hash|generalize|shift` changes how a type is written. Default remains `replace` (PERSON_1).
- `--entity-profile hipaa-safe-harbor` is a coverage aid (year-only dates, ZIP3, age 90+). Not a compliance certificate.
- National-ID regexes can be limited with `filter_regex_patterns(["US", "GB"])` or CLI `--countries US,GB`. Universal patterns always stay.

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

**Status:** done (2026-08-15) — `feat/keep-deny-lists` (PR link after open)

**Technique:** foundational NER (deny-lists / keep-lists).  
**Why:** “Apple” the fruit vs “Apple Inc.”; your own org name should stay visible.

**Do**

- `--keep-list` / `--deny-list` files (one phrase per line).
- Keep-list skips replacement. Deny-list forces an entity even if regex/LLM missed it.

**Touches:** merge step in `core.py`, CLI.  
**Prerequisite:** none.

---

### 12. Span-based replacement

**Technique:** engineering. Makes operators and generalization more correct.  
**Why:** Global string replace can change `May` inside the wrong word. Regex `finditer` offsets are thrown away today.

**Do**

- Carry `start`/`end` (per chunk, mapped back to `full_text`).
- Replace intervals, longest-first, no overlap.

**Touches:** `regex_ner.py`, `core.py`, optional LLM offsets.  
**Prerequisite:** none. Do not block other items on this.

---

### 13. TAB-style eval harness

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

**Technique:** coverage.  
**Why:** Image-only PDFs yield empty text today (`pymupdf4llm` has nothing to read).

**Do**

- Optional OCR extra (e.g. Tesseract / ocrmypdf) behind a flag or extra.
- Document that this is a new dependency and a quality/speed trade.

**Touches:** `load_and_extract.py`, extras, recipes.  
**Prerequisite:** none.

---

### 15. In-place PDF redaction

**Technique:** different product surface.  
**Why:** Today we export Markdown. Some users need black boxes on the original PDF (pixels / content streams).

**Do**

- Research PyMuPDF redaction annotations vs content-stream rewrite.
- Keep Markdown export as default. In-place is opt-in.
- Mapping must still round-trip if we claim reversibility.

**Touches:** new output path, CLI `--output-pdf`.  
**Prerequisite:** none. Large; design before coding if needed.

---

### 16. Regex-only / offline mode

**Technique:** data removal without a language model.  
**Why:** Air-gapped machines, cost, or structured logs where regex is enough.

**Do**

- `--no-llm` / profile that skips `identify_entities_with_llm`.
- Still run checksums, country filter, operators, verify, risk.
- Document that names and identity clues will be missed.

**Touches:** `core.py`, CLI, recipes.  
**Prerequisite:** none.

---

## Out of scope

| Technique | Why not as a core feature |
|---|---|
| *k*-anonymity / ℓ-diversity / *t*-closeness as a rewriter | Defined on tables of people, not narrative PDFs. Use (7) as a report. |
| Differential privacy on the document | Calibrated noise destroys prose; ε is meaningless on one contract. |
| Mix / onion routing | Communication metadata, not document PII. |
| Homomorphic encryption / MPC | Compute-on-encrypted-data; orthogonal to redaction. |
| Whole-document GAN / LLM synthetic rewrite | Memorization risk, unstable round-trip, fights reversibility. Prefer value-level fakes later. |

---

## Independence (explicit)

Every numbered item can merge with **no prerequisite PR**. Soft couplings only:

- (9) `fake` is an operator on (6).
- (12) makes (6) and (9) more correct; do not block them on it.
- (10) is cleaner after (5) if the seed map is encrypted.

---

## Definition of done (each item)

- Tests for the new behavior and for unchanged defaults.
- `uv run ruff check .` and `uv run pytest` pass.
- If user-facing: recipes (not 101) updated. No README marketing unless the feature is released and we choose to advertise it.
- This plan file updated (status / date) when an item lands.
