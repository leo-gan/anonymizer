# How PDF Anonymizer is Different

While there are many libraries for data protection, **PDF Anonymizer** is built to bridge the gap between traditional data security and modern generative AI workloads. 

Here is what makes this project different.

---

## Traditional Regex/NER vs. LLM Context Awareness

Traditional text anonymizers (like Microsoft Presidio) use regular expressions for patterns (e.g. emails) and classical Named Entity Recognition (NER) for words (e.g. names). This approach has severe limitations:

*   **Syntax Sensitivity**: A misspelled name or unusual capitalisation (e.g. "sarah connor") can cause a classical NER model to miss the identifier entirely.
*   **Identity clues (not just names)**: A sentence can point to one real person without ever writing their name. See the full explanation below.

*   **PDF Anonymizer's Advantage**: The careful (`detailed`) instructions now ask the language model to hide those identity clues, not only names, emails, and phone numbers. The faster (`simple`) instructions still look mainly for obvious labels, so they stay cheap.

---

## Identity clues: when the name is missing, but everyone still knows who it is

Imagine you are asked to hide people in a story. Crossing out every name is a good first step. It is not enough.

Suppose a classmate writes:

> "We scheduled a meeting with the CEO of Tesla at his office in Austin."

There is no first name and no last name in that sentence. A simple name-finder will miss it. Any reader who follows the news still knows exactly which person is meant.

That leftover phrase is an **identity clue**: words that do not *look* like a name, but still pick out one person.

Here are three everyday cases the careful instructions now ask the model to catch:

1. **Job + company + place.** "the CEO of Tesla … in Austin" points to one well-known person. The tool should hide the whole clue (`CEO of Tesla`), and still hide the company and the city if they appear.
2. **Author of a famous work.** "the author of the 'Harry Potter' series" points to one writer, even if the writer's name is never written.
3. **A one-of-a-kind role at a named company.** "Acme Inc.'s only in-house patent counsel" may not be a celebrity, but inside that company it still points to one employee. The tool should hide the whole phrase.

### What the tool does with a clue

- If the model **knows the person's name**, it treats the clue as that person. Later, if the real name also appears, both get the same stand-in label (for example `PERSON_1` and `PERSON_1.v_1`).
- If the model **cannot name the person**, it still hides the phrase and labels it `INDIRECT_1`. The important part is that the identifying words leave the page.

### What it should *not* hide

Vague words are not identity clues. "the CEO" by itself, or "a teacher in Austin", could be many people. The instructions tell the model to leave those alone unless the rest of the sentence makes the person unique.

### How to turn this on

The default `best-speed` profile uses the short instructions, which do **not** hunt for these clues. Use the careful profile when this matters:

```bash
pdf-anonymizer run notes.pdf -p best-quality
```

Or keep your current profile and only switch the instructions:

```bash
pdf-anonymizer run notes.pdf --prompt-name detailed
```

This is still a helper, not a guarantee. A very unusual clue can be missed. If a document must be safe to share, a person should still read the result.

After `run`, two report files help you look: `*.residual_pii.json` (leftover emails or numbers) and `*.risk.json` (identity-clue clumps such as job + company + place). They do **not** rewrite the page.

A flag-by-flag list of what landed is on the [CLI History](../project/cli-usage.md#history) page.

---

## Reversible Masking (The Mapping Engine)

Many tools simply erase text or replace it with generic masks (like `<REDACTED>`), destroying the structure and utility of the document. 

PDF Anonymizer creates **reversible placeholder mappings**:

- **Placeholders retain context**: Instead of generic redaction, identifiers are replaced with typed, incremented placeholders (e.g., `PERSON_1`, `ORGANIZATION_2`, `DATE_1`). This preserves the grammar, flow, and structural meaning of the document.
- **Separate mapping file**: The CLI outputs an anonymized document along with a JSON mapping file (e.g., `document.mapping.json`). You can lock that file as `*.mapping.json.enc` (AES-256-GCM + Argon2id) with a passphrase, or keep the map only in memory (`--ephemeral-mapping`). Default is still plaintext JSON.
- **Local Deanonymization**: You can send the anonymized document to a third party or public AI service for processing, translation, or analysis. When the results return, you run the CLI's `deanonymize` command locally with the mapping file to restore the original names.

```
[Raw Document] -> [PDF Anonymizer CLI]
                       |
        +--------------+--------------+
        |                             |
 [Anonymized Text]            [JSON Mapping File]
 (Sent to external API/Agent) (Kept in local secure vault)
        |                             |
        v                             |
 [AI-Processed Text]                  |
        |                             |
        +--------------+--------------+
                       |
                       v
         [Local Deanonymize Command]
                       |
            [Final Restored Document]
```

---

## Privacy-First and Cost-Effective

Sending sensitive documents to public cloud APIs to redact them is a security contradiction. 

*   **Local Processing**: PDF Anonymizer supports local LLM deployment out-of-the-box via **Ollama**. You can run models like `gemma` or `phi4-mini` entirely on your workstation. Your sensitive raw documents never leave your local environment.
*   **Multi-Provider Agility**: If you have access to secure enterprise cloud endpoints, you can easily toggle between providers like **Google Gemini**, **Anthropic Claude**, **OpenAI**, **Hugging Face**, and **OpenRouter** by simply changing a command option and setting your API keys in a `.env` file.

---

## Engineered for Scale (Up to 1GB)

Large documents (like a 500-page clinical trial registry or a 1GB database export in text format) exceed the maximum input size (context window) of typical LLMs, or they cause standard scripts to crash due to memory depletion.

*   **Smart Stream-Chunking**: PDF Anonymizer uses an advanced chunking system. It streams the document, breaks it down into manageable semantic slices, processes each chunk through the LLM, and stitches the results and entity mappings back together dynamically. This allows you to process large files consistently without running out of memory.

---

## Quick Comparison Summary

| Feature | Legacy Regex/NER Tools | Generic Cloud Redactors | PDF Anonymizer |
| :--- | :--- | :--- | :--- |
| **Contextual PII detection** | :x: No (Regex/Static) | :wavy_dash: Limited | :white_check_mark: Yes (LLM + identity clues) |
| **Mistyped numbers** | Often left in the clear | Varies | :white_check_mark: Hidden as `IBAN_LIKE_1` |
| **Reversibility** | :x: No | :x: No | :white_check_mark: Yes (JSON map; optional lock) |
| **How a type is written** | Usually one mask | Usually one mask | :white_check_mark: `replace` / `mask` / `hash` / `generalize` / `shift` / `fake` |
| **Leftover / linkage check** | Rare | Rare | :white_check_mark: Report files only (no auto-rewrite) |
| **Local Offline Run** | :white_check_mark: Yes | :x: No (Cloud only) | :white_check_mark: Yes (Via local Ollama models) |
| **Large File Support** | :wavy_dash: High memory usage | :x: Limited by file size limits | :white_check_mark: Yes (Streaming chunks up to 1GB) |
| **Monorepo Architecture** | :wavy_dash: Often monolithic | :x: Closed source | :white_check_mark: Yes (Separated Core SDK and CLI) |

---

Now that you understand the concepts and the value of the PDF Anonymizer project, you are ready to dive into the **[Project Developer Documentation](../project/index.md)** to install and use it.

**In this course:**  
[← Previous: Contemporary Techniques](techniques.md) | [Course Overview](index.md)
