# API Reference

This page is **automatically generated** from source code using [mkdocstrings](https://mkdocstrings.github.io/).

It reflects the current public surface of `pdf-anonymizer-core`. The hand-written usage guide is in [SDK & API Usage](api-usage.md). For practical examples see [Recipes & Common Workflows](recipes.md).

!!! info
    The CLI (`pdf-anonymizer-cli`) is a thin wrapper built with [Typer](https://typer.tiangolo.com/). Most logic lives in the core package.

---

## Core Functions

::: pdf_anonymizer_core.core.anonymize_file

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

---

## Low-Level Components (for advanced use / extension)

::: pdf_anonymizer_core.llm_provider

::: pdf_anonymizer_core.call_llm

::: pdf_anonymizer_core.load_and_extract

::: pdf_anonymizer_core.regex_ner
