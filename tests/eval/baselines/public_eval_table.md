# Public eval table

Regex-only is measured. NER waits on item 20. `detailed` LLM is nightly / opt-in.
This is not a legal privacy proof.

| Profile | Docs | Mention P | Mention R | Mention F1 | Leftover | Structured leftover | Note |
|---|---:|---:|---:|---:|---:|---:|---|
| regex-only | 6761 | 0.231 | 0.303 | 0.262 | 0.576 | 0.039 | committed baseline |
| ner | — | — | — | — | — | — | not shipped (item 20) |
| detailed-llm | — | — | — | — | — | — | opt-in / nightly; no API key in PR CI |
