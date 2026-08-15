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
- [x] 6. Generalization and per-entity operators — done 2026-08-15, `feat/entity-operators`
- [ ] 7. Quasi-identifier / linkage risk report
- [ ] 8. HIPAA Safe Harbor entity profile

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
| Re-ID / attack simulation | Residual regex scan after `run` / `verify` (`data/stats/<stem>.residual_pii.json`); deanonymize stats still `unused` / `not_found` |

Known code facts to attach to:

- `conf.py`: regexes are still structural. After a match, `validators.py` runs a cheap check (Luhn, IBAN, VIN, a few national IDs). Failures stay hidden as `TYPE_LIKE` (`IBAN_LIKE_1`).
- `core.py`: replacement is whole-document string match, not character spans.
- `prompts/detailed.py`: asks for identity clues (`INDIRECT`, or `PERSON` with a known `base_form`) plus birthdates; `simple.py` does not. Shipped in [PR #40](https://github.com/leo-gan/anonymizer/pull/40).
- Mapping files are plaintext by default. `--mapping-passphrase` / `ANONYMIZER_MAPPING_KEY` writes `*.mapping.json.enc` (AES-256-GCM).
- `--operator TYPE=mask|hash|generalize|shift` changes how a type is written. Default remains `replace` (PERSON_1).
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

**Status:** done (2026-08-15) — `feat/entity-operators` (PR link after open)

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

## Suggested later (still independent)

Do not start these until 1–8 are done or explicitly re-prioritized.

| Item | Notes |
|---|---|
| Format-preserving synthetic replacements | Seeded Faker keyed by `hash(secret, base_form, type)`. Cleaner as an operator on (6). |
| Cross-document consistent placeholders | `--mapping-in existing.mapping.json` so `John Doe` is `PERSON_1` across a batch. |
| Allowlist / denylist gazetteers | `--keep-list` / `--deny-list`. “Apple” the fruit vs “Apple Inc.” |
| Span-based replacement | Carry `start`/`end`; replace intervals, longest-first. Makes (6) more correct. |
| TAB-style eval harness | Mention-level and entity-level recall; split direct vs quasi identifiers. Tests/scripts only. |
| OCR for scanned PDFs | Coverage gap; different stack. |
| In-place PDF redaction | Different product surface (pixels / content streams), not Markdown export. |
| Regex-only / offline mode | No LLM; useful for air-gapped structured PII. |

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

- (6) synthetic `fake` (later) is cleaner as an operator.
- (8) is just config + prompt if (6) exists; without (6) it can still force type coverage.
- (7) is more useful after (1).
- Span-based replacement (later) makes (6) more correct; do not block (6) on it.

---

## Definition of done (each item)

- Tests for the new behavior and for unchanged defaults.
- `uv run ruff check .` and `uv run pytest` pass.
- If user-facing: recipes (not 101) updated. No README marketing unless the feature is released and we choose to advertise it.
- This plan file updated (status / date) when an item lands.
