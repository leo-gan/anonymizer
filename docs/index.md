# 🦉🫥 PDF Anonymizer Documentation

Welcome to the official documentation portal for the **PDF Anonymizer** project. 

PDF Anonymizer is a high-performance, developer-friendly utility and Python SDK designed to strip Personally Identifiable Information (PII) from large PDF, Markdown, and plain text documents using advanced large language models (LLMs). Crucially, the process is fully reversible: you can safely share your anonymized documents and later deanonymize them using local cryptographic maps.

<div class="grid cards" markdown="1">

-   __Privacy & Anonymization 101__

    ---

    New to privacy engineering? Take our 101 entry course. Learn why anonymization is vital, where it is used (healthcare, finance, research), contemporary tools, and how context-aware LLMs change the landscape.

    [:octicons-arrow-right-24: Start Anonymization 101](101/index.md)

-   __Project Developer Documentation__

    ---

    Ready to build or run? Explore the installation guides, CLI command reference, Python API/SDK code examples, and monorepo architectural internals.

    [:octicons-arrow-right-24: Explore Project Docs](project/index.md)

</div>

---

## Key Highlights

*   **Context-Aware Accuracy**: Traditional systems rely on regex or fixed lists (NER), missing complex references. PDF Anonymizer uses LLMs to grasp the deep semantics and context of your documents.
*   **100% Reversible**: Generate secure, deanonymizable files. Perfect for downstream workflows (like AI agents or translation) that require masking but must ultimately map back to original data.
*   **Privacy First & Cost Effective**: Fully compatible with local, offline models using **Ollama** (e.g., Gemma 2, Phi 3/4). Also supports **Google Gemini**, **Anthropic Claude**, **OpenAI GPT**, **Hugging Face**, and **OpenRouter**.
*   **Built for Scale**: Implements an intelligent stream-based chunking mechanism designed to reliably handle files up to **1GB** without running out of context windows or memory.

---

## Quick Start in 60 Seconds

Ensure you have [uv](https://astral.sh/docs/uv) installed, then sync the dependencies:

```bash
# Clone the repository
git clone https://github.com/LeoGan/anonymizer.git
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
pdf-anonymizer deanonymize data/sample.anonymized.md data/sample.mapping.json
```
