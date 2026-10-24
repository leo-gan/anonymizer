# Gold corpus and eval

This page is how we measure leftover risk. Unit tests prove that functions return the right shape. They do not prove that a real document still hides emails, cards, and names.

A [gold-corpus](terminology.md#gold-corpus) is a set of documents with labeled personal spans. We run the package on those documents and compare what it hid with what the labels say should be hidden.

The product command `run` does not change. These scripts and tests sit beside it. Words used below are defined on [Terminology](terminology.md).

This is not a legal privacy proof and not a HIPAA or GDPR certificate.

---

## Goals

| Goal | Why |
|---|---|
| Measure completeness on public anonymization tests | Competitors publish recall and leak rate. We cannot claim quality on OCR, native PDF, or a later NER stage if leftovers on a gold set never fail a test. |
| Keep PR CI cheap and deterministic | Cloud API keys are forbidden in PR CI. Regex-only is the gate. A live language model is opt-in. |
| Fail the build when structured leftovers remain | The product already writes `*.residual_pii.json`. A report that nobody reads is not a gate. |
| Cover the sectors in [Why Anonymize?](../101/why-anonymization.md) | Healthcare, legal, government, research, finance, and enterprise are the jobs users bring. |
| Keep the large public files out of git | TAB, Presidio, and Gretel are downloadable. The installer writes them under `data/gold-corpus/`, which git ignores. |

---

## What we measure

Scores follow the TAB split (mention vs entity, direct vs quasi). Definitions: [leftover](terminology.md#leftover), [gold-corpus](terminology.md#gold-corpus), [how we measure](terminology.md#how-we-measure).

**Honesty.** Each row is one run of this package, not a cross-tool ranking. The local row is RE2 plus the detailed prompt on `ollama/gemma4:12b-it-qat` (quantization-aware 4-bit, thinking off, context 8192, temperature 0), scored on 24 October 2026. The closed row stays empty until that run is approved. Do not copy these numbers onto the README as marketing.

| Profile | Docs | Mention F1 | Direct F1 | Quasi F1 | Leftover | Structured leftover |
|---|---:|---:|---:|---:|---:|---:|
| regex-only | 6761 | 0.262 | 0.293 | 0.235 | 0.576 | 0.039 |
| local-detailed | 6761 | 0.564 | 0.560 | 0.325 | 0.241 | 0.001 |

Court text is the weak slice. TAB mention F1 is 0.327 and leftover is 0.564. Gretel mention F1 is 0.703 and leftover is 0.053. The numbers live in `tests/eval/baselines/`. Pull-request CI scores regex-only on the committed fixtures and does not download a model.

---

## What is in the corpus

The catalog is `tests/eval/sources.json`.

| Source | Domain | In git? | Role |
|---|---|---|---|
| Mini-tab (`tests/eval/fixture.json`) | general | Yes | Tiny TAB-style fixture from item 13. Always in PR CI. |
| Domain pack (`tests/eval/domain_pack.json`) | healthcare, legal, government, research, finance, enterprise | Yes | Short labeled pages for the user sectors. Always in PR CI. |
| [TAB](https://github.com/NorskRegnesentral/text-anonymization-benchmark) | legal | No. Download. | Official `GoldCorpus`: English ECHR court cases. MIT. |
| [Presidio synth_dataset_v2](https://github.com/microsoft/presidio-research) | general | No. Download. | Public Presidio-class PII eval set. MIT. |
| [Gretel PII Masking EN v1](https://huggingface.co/datasets/gretelai/gretel-pii-masking-en-v1) (test) | many industries | No. Download. | 5,000 synthetic documents. Apache-2.0. |
| i2b2/n2c2, MIMIC, Kaggle PII, MAPA | healthcare, research, government | No | Need a login or a data-use agreement. Listed only. Not fetched. |

Downloaded files land in `data/gold-corpus/raw/` and a normalized JSONL view in `data/gold-corpus/normalized/`. Git ignores `/data/`.

---

## Workflows

### 1. Install the public tests

```bash
make gold-corpus
# or
uv run python scripts/download_gold_corpus.py
```

Default fetch: TAB test + dev, Presidio synth, Gretel test. Add `--full` for TAB train (about 48 MB extra).

### 2. Score the package (regex-only baseline)

```bash
make gold-bench
# or
uv run python scripts/run_gold_benchmark.py --write-baseline
```

This runs `extract_entities_via_regex` and `anonymize_text_content(..., use_llm=False)`. It writes `tests/eval/baselines/gold_corpus_regex_only.json`. No API key is required.

### 2b. Score `id-extract` alone

```bash
make gold-bench-id-extract
# or
uv run python scripts/run_id_extract_benchmark.py --write-baseline
```

This calls `id_extract.extract` only. It does not replace text or write a mapping. It writes `tests/eval/baselines/gold_corpus_id_extract.json`. Use that file to improve the detector without going through core. Default sources are the committed CI set (`mini-tab`, `domain-pack`).

### 3. Print the public eval table

```bash
make gold-table
# or
uv run python scripts/eval_public_table.py
```

The table is `tests/eval/baselines/public_eval_table.md`. A language-model row appears after `scripts/run_gold_benchmark.py --profile local-detailed` or `--profile closed-detailed` writes its baseline. Those runs are not part of PR CI.

### 4. PR CI completeness gate

`.github/workflows/ci.yml` runs `make test-cov`. That job includes:

| Gate | What fails the build |
|---|---|
| System test | Structured mention recall below 1.0, or structured leftover above 0, on mini-tab + domain pack. |
| Red-team | `*.residual_pii.json` still contains a structured identifier. |
| Coverage | Line coverage below 70% (first measured run was 77%; the floor is not “90%”). |
| Fuzz | `tests/test_fuzz.py`: regex NER, mapping envelopes, PDF bytes, CSV bytes. A zero-page PDF must not look like a successful empty extract. |

The large downloaded sets are **not** required in PR CI. If they are present locally, an extra test checks that structured leftover on a sample stays at or under 10%.

### 5. Tiny fixture only

```bash
uv run python scripts/eval_tab.py
```

This scores `tests/eval/fixture.json` the same way as item 13. Use it when you only need the scorer, not the public corpus.

---

## Layout

```text
scripts/download_gold_corpus.py      # install (gitignored data)
scripts/run_gold_benchmark.py        # score + leftover
scripts/eval_public_table.py         # regex vs NER vs LLM table
scripts/eval_tab.py                  # mini fixture only
tests/eval/gold.py                   # converters, leftover, gates
tests/eval/sources.json              # catalog
tests/eval/domain_pack.json          # committed use-case pages
tests/eval/fixture.json              # mini-tab
tests/eval/baselines/                # committed scores, not the documents
tests/eval/test_completeness.py      # CI leftover / recall / residual JSON
tests/test_fuzz.py                   # Hypothesis
data/gold-corpus/                    # downloaded files (not in git)
```

---

## See also

- [Terminology](terminology.md) — leftover, mention, quasi-identifier, TAB
- [Recipes](recipes.md#gold-corpus-benchmark) — the same commands in the recipe list
- [Why Anonymize?](../101/why-anonymization.md) — sectors the domain pack covers
- Improvement-plan item 19 (maintainers only, not on this site)
