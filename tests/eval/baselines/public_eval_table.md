# Public eval table

Regex-only is the offline gate. NER, local detailed, and closed detailed
appear when their baseline files exist. This is not a legal privacy proof.

| Profile | Model | Docs | Mention P | Mention R | Mention F1 | Entity F1 | Direct F1 | Quasi F1 | Leftover | Structured leftover | Note |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| regex-only | — | 6761 | 0.231 | 0.303 | 0.262 | 0.295 | 0.293 | 0.235 | 0.576 | 0.039 | committed baseline |
| ner | — | — | — | — | — | — | — | — | — | — | not measured on this machine |
| local-detailed | ollama/gemma4:12b-it-qat | 6761 | 0.506 | 0.638 | 0.564 | 0.440 | 0.560 | 0.325 | 0.241 | 0.001 | RE2 + detailed prompt, think off, num_ctx 8192 |
| closed-detailed | — | — | — | — | — | — | — | — | — | — | not run; closed model not approved yet |
