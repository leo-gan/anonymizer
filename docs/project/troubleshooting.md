# Troubleshooting

Common problems and how to resolve them.

## Authentication / Missing API Key

- **Symptom**: Errors like "GOOGLE_API_KEY not found", "HUGGING_FACE_TOKEN environment variable not set", or provider import failures.
- **Fix**:
  - Create a `.env` file in the directory where you run the command (or a parent directory).
  - The CLI automatically loads it. Example:

    ```env
    GOOGLE_API_KEY="AIza..."
    OPENAI_API_KEY="sk-..."
    ANTHROPIC_API_KEY="sk-ant-..."
    HUGGING_FACE_TOKEN="hf_..."
    OPENROUTER_API_KEY="sk-or-..."
    OLLAMA_HOST="http://localhost:11434"
    ```
  - For the SDK, load the environment variables yourself (e.g. with `python-dotenv` or `os.environ`).

## Ollama Not Running or Model Not Found

- **Symptom**: Connection errors or "model not found" when using `ollama/...` models.
- **Fix**:
  - Start the Ollama server: `ollama serve`
  - Pull the model first: `ollama pull phi4-mini` or `ollama pull gemma:7b`
  - Check `OLLAMA_HOST` if Ollama is not on the default port.

## Rate Limits, Timeouts, or Retries

- **Symptom**: Intermittent failures, "rate limit", 429, or empty results on long documents.
- **Fix**:
  - Use a more generous profile: `-p best-quality` (more retries, smaller chunks).
  - Or override manually with a larger model / more retries via SDK `max_retries`.
  - The library uses exponential backoff + jitter for transient errors (rate limits, server errors, connection issues, JSON parse errors). Auth errors are not retried.

## Nothing Was Anonymized / Very Few Entities Found

- **Symptom**: Output looks almost identical to the input.
- **Possible causes & fixes**:
  - The document contains very little PII (or the LLM prompt style was too conservative).
  - Try `-p best-quality` (uses the `detailed` prompt and a stronger model by default).
  - Use `--anonymized-entities` only if you intentionally want to restrict the types.
  - Check `app.log` — it shows how many entities were found by Regex vs LLM per chunk.
  - Very short documents or unusual formatting can reduce recall.

## LLM Returns Invalid JSON / Parsing Failures

- **Symptom**: Errors about JSON decode or Pydantic validation in the logs.
- **Fix**:
  - The library already retries on parsing errors (the LLM sometimes returns markdown fences or extra text).
  - If it keeps happening, switch to a stronger model (`-p best-quality`) or a model known to follow JSON instructions well.
  - The prompts are designed to return only a JSON object.

## Cache Problems or Stale Results

- **Symptom**: Changes to prompts or documents are ignored, or you want a completely fresh run.
- **Fix**:
  - Delete or rename `data/cache/llm_responses.json`.
  - Or disable caching programmatically:

    ```python
    from pdf_anonymizer_core.llm_provider import configure_cache
    configure_cache(enabled=False)
    ```

## Large Files / Memory or Context Issues

- **Symptom**: Out of memory, context length errors, or very slow runs.
- **Fix**:
  - Use `-p best-cost` (larger chunks).
  - Manually increase `--characters-to-anonymize` (e.g. 120000 or higher) when using a model with a large context window.
  - The tool uses Markdown-aware splitting for PDFs and `.md` files to preserve structure.

## Output Files Not Where Expected

- All artifacts are written relative to the current working directory:
  - `data/anonymized/`
  - `data/mappings/`
  - `data/deanonymized/`
  - `data/stats/`
- These directories are created automatically.

## Still Stuck?

1. Look at `app.log` (always written alongside console output).
2. Run with a small test file and `-p best-quality`.
3. Check the [Recipes & Common Workflows](recipes.md) page for working examples.
4. Open an issue on GitHub with the log output and the exact command you ran.

---

---

## See Also

- **[Recipes & Common Workflows](recipes.md)** — many of the issues here are demonstrated with working examples.
- **[CLI Reference](cli-usage.md)** — full command options and profiles.
- **[Architecture Design](architecture.md)** — deeper internals that can help understand error cases.
- **[SDK & API Usage](api-usage.md)** — programmatic usage.
