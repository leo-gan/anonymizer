# 🦉🫥 PDF Anonymizer Documentation

This tool hides personal details in documents and can put them back. It is a reversible document [pseudonymizer](project/terminology.md), not a legal certificate.

<div class="grid cards" markdown="1">

-   __Privacy & Anonymization 101__

    ---

    New to privacy engineering? Take our 101 entry course. Learn why anonymization is vital, where it is used (healthcare, finance, research), contemporary tools, and how context-aware LLMs change the landscape.

    [:octicons-arrow-right-24: Start Anonymization 101](101/index.md)

-   __Project Developer Documentation__

    ---

    Ready to build or run? Explore the installation guides, CLI command reference, Python API/SDK code examples, **practical recipes & workflows**, and monorepo architectural internals.

    [:octicons-arrow-right-24: Explore Project Docs](project/index.md)

</div>

---

## What it does

| Feature | Meaning |
|---|---|
| Reversible pseudonymization | Personal values become typed placeholders (`PERSON_1`) plus a mapping file. This is not irreversible anonymization. |
| Hybrid named-entity recognition | RE2 regular expressions find structured identifiers; a language model finds names. Optional local span NER (GLiNER). |
| Checksums | A failed Luhn or IBAN check is still hidden as `IBAN_LIKE`, so leftover digits do not stay visible. |
| Identity clues | The careful profile also hides phrases that pick out one person without a name (quasi-identifiers, type `INDIRECT`). |
| Leftover measurement | Residual scan after masking. Gold-corpus leftover rate and recall in CI, split like TAB into direct vs quasi identifiers. |
| Anonymization statistics | After a run, `data/stats/` records leftovers (`*.residual_pii.json`) and linkage-risk clumps (`*.risk.json`). Deanonymize writes unused and missing mapping counts. |
| Span-based replacement | Replacement is by character interval. The longer span wins when two hits overlap. |
| File types | PDF, Markdown, plain text, CSV, Excel, and Word (`.docx`). |
| Country-specific PII | National-ID regexes for 30+ countries (US, CA, GB, ES, IT, FR, IN, CN, and others). `--countries US,GB` keeps only those national IDs. Email, IBAN, and cards always stay. |
| HIPAA Safe Harbor aid | `--entity-profile hipaa-safe-harbor` covers the 18 identifier classes (year-only dates, ZIP3, age 90+). It is a coverage aid, not a compliance certificate. |
| OCR | `--ocr` runs Tesseract when a PDF has pages but no text layer. |
| Local or remote | Ollama on this machine, or Gemini, OpenAI, Anthropic, Hugging Face, OpenRouter. |

Operators, locked maps, and HTTP are in [Project Docs](project/index.md) and [Recipes](project/recipes.md).

---

## Quick Start in 60 Seconds

Ensure you have [uv](https://astral.sh/docs/uv) installed, then sync the dependencies:

```bash
# Clone the repository
git clone https://github.com/leo-gan/anonymizer.git
cd anonymizer

# Install all development dependencies (including support for all LLM providers)
uv sync --group dev
```

Now you can anonymize your first file (default uses Google Gemini, make sure `GOOGLE_API_KEY` is in your `.env`):

```bash
# Anonymize a PDF
pdf-anonymizer run data/sample.pdf
```

To deanonymize the file later:

```bash
# Revert the anonymization
pdf-anonymizer deanonymize \
  data/anonymized/sample.anonymized.md \
  data/mappings/sample.mapping.json
```

---

## Interactive Demo Example

We provide a pre-built example containing hybrid NER (Regex + LLM) and full round-trip verification:

1. **Prepare the PDF**: Downloads an open-access arXiv research paper and writes synthetic PII (name, email, phone, IP, SSN) onto the first page:
   ```bash
   uv run python scripts/prepare_demo_pdf.py
   ```

2. **Execute Anonymization & Deanonymization**: Runs the pipeline and asserts correctness, printing the original, anonymized, and recovered text:
   ```bash
   uv run python scripts/demo_anonymize.py
   ```

For many more real-world usage patterns (local-only processing, locked maps, operators, HIPAA coverage aid, keep/deny lists, leftover checks, batch jobs, eval harness, troubleshooting, etc.) see the dedicated **[Recipes & Common Workflows](project/recipes.md)**, **[Gold corpus & eval](project/gold-corpus.md)**, **[Terminology](project/terminology.md)**, and **[Troubleshooting](project/troubleshooting.md)** pages. An auto-generated **[API Reference](project/api-reference.md)** is also available. The CLI **[History](project/cli-usage.md#history)** lists what landed, flag by flag.
