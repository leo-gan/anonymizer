# State-of-the-art comparison (merged research)

**Status:** living research note  
**Audience:** maintainers only  
**Do not publish.** This directory is excluded from the MkDocs / GitHub Pages build.

Sources merged here:

1. Session research (product docs + deep-research workflow, 2026-09-03).
2. `docs/temp/Anonymizer Tool Competitive Analysis.md` — same-class de-identification suite analysis.
3. `docs/temp/deep-research-report (7).md` — OS / network anonymity survey (Tails, Whonix, Qubes, Tor, MAT, …).

Claims from (3) that contradict this repo are marked **corrected** below. Do not treat that report as an inventory of this codebase.

---

## What this product is

PDF Anonymizer (v0.17) is a **reversible document / table pseudonymizer**:

- Hybrid RE2 (70+ patterns, 30+ countries, checksums, `TYPE_LIKE`) + LLM NER
- Identity clues in the `detailed` prompt (`INDIRECT` / known `base_form`)
- Typed stand-ins (`PERSON_1`) + JSON map (optional AES-256-GCM + Argon2id, ephemeral)
- Operators: `replace` / `mask` / `hash` / `generalize` / `shift` / `fake`
- Residual-PII verify and linkage-risk reports (**report only**)
- HIPAA Safe Harbor **aid**, not a certificate
- PDF/MD/TXT via `pymupdf4llm` **Markdown export**; CSV/XLSX **per-cell** (not flattened text, not *k*-anonymity)
- Local Ollama, `--no-llm` / `regex-only`, plus cloud providers
- Chunked processing claimed to 1GB

It is **not** an anonymity OS, a Tor wrapper, or a statistical disclosure-control engine.

---

## Landscape (three classes, not one table)

| Class | Examples | Competes with this repo? |
|---|---|---|
| Document / text de-identification | Presidio, Philter/Phileas, Azure Language PII, Limina/Private AI, Skyflow Detect, Tonic Textual, Redactable, Adobe Redact | **Yes** — same user job |
| Tabular / synthetic privacy | ARX, Tonic Structural, MOSTLY AI, Gretel, pgEdge-anonymizer, Greenmask | **Adjacent** for CSV/XLSX only |
| OS / network anonymity | Tails, Whonix, Qubes, Tor Browser, I2P, ProtonVPN, AnonSurf, OnionShare, Ricochet | **No** — different threat model |

The OS/network survey is useful only for **adjacent hygiene**: metadata wipe, sandboxing untrusted PDFs, no-telemetry policy, reproducible releases. It is not a feature backlog for Tor, live USB, or browser fingerprinting.

---

## Corrections to the temp reports

| Temp-doc claim | Fact in this repo |
|---|---|
| No offline / local LLM; must send data to the cloud | **False.** Ollama extras, `--no-llm` / `-p regex-only`. Cloud is optional. |
| Core depends on spaCy | **False.** No spaCy dependency. Semantic stage is LLM, not spaCy NER. |
| CSV/Excel treated as one continuous text stream | **False.** `tables.py` is per-cell regex + row-addressed LLM batches. Still not *k*-anonymity. |
| No CI | **Partial.** Lint workflow badge exists; coverage/reproducible-release story is still thin. |
| No local execution / amnesic mode at all | **Partial.** `--ephemeral-mapping` keeps the map in memory. Outputs still land on disk unless the user deletes them. |
| Should become Tails/Whonix/Qubes-like | **Out of class.** Do not add Tor routing, amnesic live OS, or VM isolation as product features. |

---

## Head-to-head (document class)

| Capability | This distro | Presidio | Philter / Phileas | Azure Document PII | Limina / Skyflow / Redactable |
|---|---|---|---|---|---|
| Hybrid regex + checksums | Yes (RE2, `TYPE_LIKE`) | Yes | Yes | Cloud NER | Mix of ML + patterns |
| Identity clues / quasi-IDs | **Yes (detailed + risk.json)** | Custom rules | Conditions | Weak | Vendor “context” claims |
| Reversible typed map + lock | **Yes** | Encrypt/decrypt ops | FPE / encrypt | Mask / synthetic | Vault tokens or permanent wipe |
| Native PDF out + metadata wipe | **No — Markdown** | Image raster redaction | Native PDF | Layout-preserving PDF/DOCX | Rasterize-rebuild or true redact + Sanitize |
| OCR / scans / faces | **No** (silent empty extract) | Tesseract / Azure DI, DICOM pixels | On-device OCR | Scanned PDF + blur | OCR + faces/logos/signatures |
| Local span NER (GLiNER/spaCy) | **No** (LLM or regex) | spaCy / transformers | Ph-Eye GLiNER | Cloud | Purpose-trained models |
| Confidence 0–1 + recognizer id | **No** (binary + reports) | Yes | Sensitivity levels | Yes | Yes |
| FPE / NIST FF3 / vault re-id | **No** (map file) | Encrypt | FPE | No | Skyflow / Tonic FPE |
| HTTP API / Docker service | **CLI + SDK only** | Analyzer/Anonymizer services | API + Desktop | REST | SaaS / container |
| Review / apply leftovers | Report only | None | Policy + Desktop | Playground | HITL wizard |

Tabular-only: ARX / Tonic / Gretel / MOSTLY AI add *k*-anonymity, ℓ-diversity, *t*-closeness, (ε, δ)-DP, Prosecutor/Journalist/Marketer risk, and FK-preserving FPE at >20k rows/s. This repo’s Excel/CSV path does not.

---

## Highest-impact gaps (merged ranking)

Ranked for **this product becoming best in its class** (reversible, local, document + LLM anonymizer). Not a DLP crawler. Not Tails.

### P0 — users cannot ship the file they opened

1. **Native vector PDF write + hidden-object sanitization**  
   Markdown export drops layout, fonts, headers, multi-column geometry. Overlay black boxes without rewriting `/Contents` leave selectable text. Adobe Sanitize, Redactable, and the competitive analysis all require: glyph excision from the content stream, orphan font cleanup, XMP + `/Info` wipe, `/Prev` incremental-save history, attachments, hidden layers, annotations, thumbnails.  
   Limina’s rasterize-each-page path is a valid *fallback* for scans; vector rewrite is the default for digital PDFs.  
   Already improvement-plan item 15.

2. **OCR for scanned / image-only pages**  
   `pymupdf4llm` on a flattened scan is an empty string — a **silent compliance miss**, not a hard error. Presidio Image Redactor, Redactable (deskew/denoise first), Skyflow (faces/logos/signatures), Tonic Textual (PNG/JPG/TIF), and the competitive analysis (PaddleOCR / Surya / Docling → bounding boxes) all treat this as table stakes.  
   Already improvement-plan item 14.

### P0 — detection quality and cost

3. **Three-tier detector: RE2 → GLiNER → LLM**  
   Today `best-speed` still calls an autoregressive model. Competitive analysis and Philter agree: GLiNER-class span models (nvidia/gliner-PII, GLiNER2-PII, Ph-Eye) do Person/Org/Loc/PHI in one forward pass on CPU. LOGICAL (arXiv:2510.19346) reports micro-F1 **0.980** on a psychiatric EHR set vs Gemini-Pro-2.5 **0.845**, with 95% of notes fully clean. GLiNER2-PII reports SPY span F1 **0.477** vs OpenAI Privacy Filter **0.380** (precision still ~0.35 — keep residual verify).  
   Keep the LLM **only** for identity clues and low-confidence spans.

4. **Per-span confidence + recognizer provenance**  
   Presidio emits 0–1 scores and which recognizer fired. This pipeline’s LLM JSON is uncalibrated. Needed to gate Tier 3 and to let `--min-confidence` replace prompt-tweaking.

### P1 — close the loop and embed

5. **Apply residuals / review UI**  
   `*.residual_pii.json` and `*.risk.json` do not rewrite. Commercial tools apply. Minimum: accept/skip spans, then rewrite.

6. **HTTP API + Docker (and AppArmor profile)**  
   Presidio and Philter are services. The OS report’s “isolate execution” point is valid for **untrusted PDFs** (malformed input, not Tor). FastAPI + one compose file is the productization of the SDK. Spark/Ray/DuckDB UDFs can wait.

7. **Public eval table + testing that can back a “best in class” claim**  
   Regex-only vs GLiNER vs `detailed` LLM; mention vs entity; direct vs quasi. Without numbers, identity-clue claims are unprovable.

   The OS-report “Testing Gaps” item is real, but narrower than that write-up said. This repo already has a large unit suite, PR CI (`ci.yml` runs `make test`), mocked pipeline tests (`test_large_pdf`, `test_main`), and a TAB-style harness (`tests/eval/`, improvement-plan item 13). What it still lacks:

   - **System / gold-corpus E2E:** anonymize a labeled dataset and assert completeness (mention/entity recall, leftover rate). Today the eval fixture scores *metrics code* and the *regex* stage; the LLM path is mocked, so quality is unmeasured.
   - **Coverage in CI:** pytest runs; there is no coverage gate or published % (the “≥ 90%” target in the OS report is a process metric, not a product feature).
   - **Fuzz / malformed input:** no hypothesis/Atheris-style fuzz of RE2 patterns, PDF bytes, or mapping envelopes. Untrusted PDFs are a real crash/ReDoS surface even with RE2.
   - **Red-team leftover pass:** a scripted attack on anonymized output (residual regex + optional LLM verify) on held-out docs — the product already *emits* `residual_pii.json`; tests do not fail the build when leftovers remain on a gold set.

   Complexity is medium; user-facing risk of *not* doing it is that OCR, native PDF, and GLiNER can ship as features nobody can prove. Treat this as the measurement spine for gaps 1–6, not a substitute for them.

### P1 — cryptography that is not a lookup file

8. **FPE (NIST SP 800-38G AES-FF3-1) and/or `encrypt` operator**  
   A passphrase-locked `mapping.json.enc` is a single point of failure: leak the map, reverse every document. Google AES-SIV / FPE-FFX, Philter FPE, Tonic FPE, and Skyflow vault IDs keep format and referential integrity **without** a central plaintext dictionary. Optional later: envelope keys via KMS/HSM instead of `ANONYMIZER_MAPPING_KEY`.

### P2 — formats and tabular honesty

9. **DOCX, then HTML/JSON**  
   Azure and Philter Desktop already do native Word. Email (`.eml`/`.msg`) after that.

10. **Optional tabular privacy engine (separate from the prose path)**  
    Do **not** run *k*-anonymity on narrative PDFs (existing out-of-scope). For CSV/XLSX/Parquet only: classify direct vs quasi IDs; FPE on directs; optional *k*/ℓ/*t* or DP on quasis; keep FK consistency across multi-table exports. Upgrade `report` toward Prosecutor / Journalist / Marketer probabilities **on tables**.

### P2 — release hygiene (from the OS survey, filtered)

11. **MAT-style metadata scrub on every output** (even Markdown/CSV: strip sidecar EXIF if images appear). Overlaps P0 item 1 for PDF.
12. **Reproducible release** (pin `uv.lock` in CI, publish wheel checksums / attestations).
13. **Written no-telemetry / data-handling policy** in README (already true in code; not stated as a guarantee).
14. **Independent code review** focused on mapping-key handling and cloud-LLM leakage — not a “become Tails” audit.

### Out of class (do not add)

- Tor / I2P / VPN / bridges / DNS-leak features
- Live-USB amnesic OS, Qubes, browser fingerprinting
- Audio / video as a core format (Limina/Skyflow/CaseGuard — different product)
- Org-wide S3/share discovery (Macie, Purview, Nightfall)
- Claiming a HIPAA *certificate* (HHS does not certify products)

---

## What to keep and advertise

These still do not appear together in Presidio, Philter, or the cloud DLP APIs:

- Identity clues + linkage-risk report
- Reversible typed vocabulary with Argon2id, AAD, ephemeral maps, deanonymize stats
- `TYPE_LIKE` (mistyped structured IDs stay hidden)
- Honest “aid, not a certificate” HIPAA language
- Local + regex-only air-gap + large-file chunking

---

## Recommended build order (reconciled)

Matches `improvement-plan.md` items 14–15, then inserts from both temp docs:

| Order | Work | Source |
|---|---|---|
| 1 | OCR extra; fail loudly on empty extract | Plan #14 + both temp docs |
| 2 | Opt-in native PDF (vector redact + Sanitize-class wipe) | Plan #15 + competitive analysis |
| 3 | GLiNER (or equivalent) as `best-speed`; LLM for clues / low confidence | Competitive analysis + Philter + GLiNER benches |
| 4 | Confidence on every span | Competitive analysis + Presidio |
| 5 | FastAPI + Docker (+ optional AppArmor) | Competitive analysis + OS report (sandbox only) |
| 6 | Review/apply residuals | Session research |
| 7 | Public eval table + gold E2E, CI coverage, PDF/regex fuzz, leftover red-team | OS-report testing gap + session eval item |
| 8 | `encrypt` / AES-FF3-1 FPE | Competitive analysis + Google/Philter/Tonic |
| 9 | DOCX | Azure / Philter Desktop |
| 10 | Optional table-only *k*/FPE engine | Competitive analysis; keep PDF out of scope |
| 11 | Release attestations + no-telemetry statement | OS report (filtered) |

---

## Temp-doc roadmaps (kept / dropped)

**Competitive analysis four phases** — keep the shape, shrink the first ship:

- Phase 1 (detect): three-tier + confidence — **keep**
- Phase 2 (PDF): vector DOM + OCR + metadata — **keep**
- Phase 3 (tables): FPE + formal privacy — **keep as optional table path only**
- Phase 4 (mesh): gRPC, Spark/Ray/DuckDB, KMS, Prosecutor models — **defer** until API + Docker exist

**OS-report Gantt** — keep metadata scrub, Docker isolation, reproducible builds, audit, packaging. Drop Tor bundling, amnesic live OS, “partnerships with privacy OSes” as product work. Local LLM is **already shipped** (mark that milestone done).
