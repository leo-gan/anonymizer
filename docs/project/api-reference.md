# API Reference

This page is **automatically generated** from source code using [mkdocstrings](https://mkdocstrings.github.io/).

It reflects the current public surface of `pdf-anonymizer-core`. The hand-written usage guide is in [SDK & API Usage](api-usage.md). For practical examples see [Recipes & Common Workflows](recipes.md).

!!! info
    The CLI (`pdf-anonymizer-cli`) is a thin wrapper built with [Typer](https://typer.tiangolo.com/). Most logic lives in the core package.

---

## Core Functions

::: pdf_anonymizer_core.core.anonymize_file

::: pdf_anonymizer_core.core.anonymize_tabular_file

::: pdf_anonymizer_core.core.anonymize_docx_file

::: pdf_anonymizer_core.utils.deanonymize_file

::: pdf_anonymizer_core.utils.consolidate_mapping

::: pdf_anonymizer_core.utils.save_results

---

## Configuration & Models

::: pdf_anonymizer_core.conf

---

## Prompts

The package ships two ready-to-use prompt templates.

::: pdf_anonymizer_core.prompts.detailed

::: pdf_anonymizer_core.prompts.simple

::: pdf_anonymizer_core.prompts.hipaa

---

## Detection, operators, and reports

::: pdf_anonymizer_core.regex_ner

::: pdf_anonymizer_core.validators

::: pdf_anonymizer_core.operators

::: pdf_anonymizer_core.spans

::: pdf_anonymizer_core.gazetteers

::: pdf_anonymizer_core.verify

::: pdf_anonymizer_core.risk

::: pdf_anonymizer_core.mapping_crypto

---

## Low-Level Components (for advanced use / extension)

::: pdf_anonymizer_core.llm_provider

::: pdf_anonymizer_core.call_llm

::: pdf_anonymizer_core.load_and_extract

::: pdf_anonymizer_core.span_ner.extract_entities_via_ner

::: pdf_anonymizer_core.span_ner.resolve_semantic_stages

::: pdf_anonymizer_core.pdf_ocr.ocr_pdf

::: pdf_anonymizer_core.pdf_ocr.write_layout_sidecar

::: pdf_anonymizer_core.pdf_output.write_anonymized_pdf

::: pdf_anonymizer_core.pdf_output.sanitize_pdf

---

## Tables (CSV / Excel)

::: pdf_anonymizer_core.tables.load_table

::: pdf_anonymizer_core.tables.save_table

::: pdf_anonymizer_core.tables.apply_mapping_to_table

::: pdf_anonymizer_core.tables.flatten_table_for_review

::: pdf_anonymizer_core.tables.load_review_text

---

## Word (DOCX)

::: pdf_anonymizer_core.word.load_docx

::: pdf_anonymizer_core.word.save_docx

::: pdf_anonymizer_core.word.apply_mapping_to_docx

::: pdf_anonymizer_core.word.flatten_docx_for_review
