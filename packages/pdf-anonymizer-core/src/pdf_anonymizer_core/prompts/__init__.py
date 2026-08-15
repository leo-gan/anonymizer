"""Prompt templates for the LLM anonymization stage.

Exposes ready-to-use templates:

- `detailed` : richer instructions, base_form support, more entity types,
  including INDIRECT (phrases that identify a person without naming them).
- `simple`   : minimal, faster, lower token usage.
- `hipaa`    : coverage aid for HIPAA Safe Harbor identifier classes.
  Not a compliance certification.

Example:
    from pdf_anonymizer_core.prompts import detailed
    prompt = detailed.prompt_template
"""

from . import detailed, hipaa, simple

__all__ = ["detailed", "hipaa", "simple"]
