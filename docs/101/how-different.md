# How PDF Anonymizer is Different

While there are many libraries for data protection, **PDF Anonymizer** is built to bridge the gap between traditional data security and modern generative AI workloads. 

Here is what makes this project different.

---

## 1. Traditional Regex/NER vs. LLM Context Awareness

Traditional text anonymizers (like Microsoft Presidio) use regular expressions for patterns (e.g. emails) and classical Named Entity Recognition (NER) for words (e.g. names). This approach has severe limitations:

*   **Syntax Sensitivity**: A misspelled name or unusual capitalisation (e.g. "sarah connor") can cause a classical NER model to miss the identifier entirely.
*   **Indirect Identifiers**: Traditional tools cannot identify contextual PII. For instance, in:

    > *"We scheduled a meeting with the CEO of Tesla at his office in Austin."*

    A classical tool might mask "Austin", but it won't mask *"CEO of Tesla"*, which immediately identifies **Elon Musk** to any reader.

*   **PDF Anonymizer's Advantage**: By leveraging Large Language Models (LLMs), the tool acts like a human reader. It understands semantics, indirect references, and complex sentence structures, allowing it to catch hidden or contextual PII that rules miss.

---

## 2. Reversible Masking (The Mapping Engine)

Many tools simply erase text or replace it with generic masks (like `<REDACTED>`), destroying the structure and utility of the document. 

PDF Anonymizer creates **reversible placeholder mappings**.

1.  **Placeholders retain context**: Instead of generic redaction, identifiers are replaced with typed, incremented placeholders (e.g., `[PERSON_1]`, `[COMPANY_2]`, `[DATE_1]`). This preserves the grammar, flow, and structural meaning of the document.
2.  **Separate Cryptographic Map**: The CLI outputs an anonymized document along with a JSON-formatted mapping file (e.g., `document.mapping.json`).
3.  **Local Deanonymization**: You can send the anonymized document to a third party or public AI service for processing, translation, or analysis. When the results return, you run the CLI's `deanonymize` command locally with the mapping file to restore the original names.

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

## 3. Privacy-First and Cost-Effective

Sending sensitive documents to public cloud APIs to redact them is a security contradiction. 

*   **Local Processing**: PDF Anonymizer supports local LLM deployment out-of-the-box via **Ollama**. You can run models like `gemma` or `phi4-mini` entirely on your workstation. Your sensitive raw documents never leave your local environment.
*   **Multi-Provider Agility**: If you have access to secure enterprise cloud endpoints, you can easily toggle between providers like **Google Gemini**, **Anthropic Claude**, **OpenAI**, **Hugging Face**, and **OpenRouter** by simply changing a command option and setting your API keys in a `.env` file.

---

## 4. Engineered for Scale (Up to 1GB)

Large documents (like a 500-page clinical trial registry or a 1GB database export in text format) exceed the maximum input size (context window) of typical LLMs, or they cause standard scripts to crash due to memory depletion.

*   **Smart Stream-Chunking**: PDF Anonymizer uses an advanced chunking system. It streams the document, breaks it down into manageable semantic slices, processes each chunk through the LLM, and stitches the results and entity mappings back together dynamically. This allows you to process large files consistently without running out of memory.

---

## Quick Comparison Summary

| Feature | Legacy Regex/NER Tools | Generic Cloud Redactors | PDF Anonymizer |
| :--- | :--- | :--- | :--- |
| **Contextual PII detection** | :x: No (Regex/Static) | :wavy_dash: Limited | :white_check_mark: Yes (LLM semantic comprehension) |
| **Reversibility** | :x: No | :x: No | :white_check_mark: Yes (Separate JSON maps) |
| **Local Offline Run** | :white_check_mark: Yes | :x: No (Cloud only) | :white_check_mark: Yes (Via local Ollama models) |
| **Large File Support** | :wavy_dash: High memory usage | :x: Limited by file size limits | :white_check_mark: Yes (Streaming chunks up to 1GB) |
| **Monorepo Architecture** | :wavy_dash: Often monolithic | :x: Closed source | :white_check_mark: Yes (Separated Core SDK and CLI) |

---

Now that you understand the concepts and the value of the PDF Anonymizer project, you are ready to dive into the **[Project Developer Documentation](../project/index.md)** to install and use it.
