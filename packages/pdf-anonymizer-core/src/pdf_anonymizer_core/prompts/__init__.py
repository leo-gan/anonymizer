"""Prompt templates for the LLM anonymization stage.

Exposes two ready-to-use templates:

- `detailed` : richer instructions, base_form support, more entity types.
- `simple`   : minimal, faster, lower token usage.

Example:
    from pdf_anonymizer_core.prompts import detailed
    prompt = detailed.prompt_template
"""

from . import detailed, simple

__all__ = ["detailed", "simple"]
