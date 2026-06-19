# Contemporary Anonymization Techniques & Tools

Over the past few decades, computer scientists and statisticians have developed a variety of frameworks to hide identities in datasets. Let's compare these contemporary techniques and review legacy tooling.

---

## Traditional & Cryptographic Methods

These are the most common methods used in databases and structured logs.

### A. Data Masking & Redaction
Replacing characters with a generic symbol (e.g. replacing a Credit Card Number with `XXXX-XXXX-XXXX-1234`).

*   **Pros**: Easy to implement; retains the format of the data.
*   **Cons**: Completely destroys the masked information. Cannot be reversed.

### B. Hashing & Tokenization
Passing PII through a cryptographic hash function (e.g., SHA-256) or replacing it with a randomly generated token.

*   **Pros**: Pseudonymized identifiers remain consistent (the same name always produces the same hash).
*   **Cons**: Subject to dictionary attacks if the salt is weak or missing; does not solve the context leakage problem in free text.

---

## Statistical Privacy Models

For structured tables (like Excel or SQL tables), researchers use mathematical parameters to measure privacy strength.

```
       [Raw Database Table]
                |
   +------------+------------+
   |  k-Anonymity            |  l-Diversity            |  t-Closeness
   v                         v                         v
Ensure records match      Ensure sensitive value    Ensure distribution
at least k-1 others       is diverse in each group  matches global pool
```

### A. *k*-Anonymity
A dataset satisfies *k*-anonymity if the information for each person contained in the release cannot be distinguished from at least *k*-1 other individuals whose information also appears in the release.

*   *Example*: If *k*=5, you can only filter the table down to a group of 5 identical rows (e.g. 5 males, aged 30-35, living in zip code 90210).

### B. *l*-Diversity
An extension of *k*-anonymity. Within each group of *k* matching records, there must be at least *l* distinct values for any sensitive attributes (such as medical diagnosis). This prevents attackers from guessing the truth if every person in that group happens to have the same disease.

### C. *t*-Closeness
A further extension of *l*-diversity. It requires that the distribution of a sensitive attribute in any group is close to the distribution of the attribute in the entire dataset.

---

## Advanced Modern Privacy Paradigms

For highly sensitive large-scale analytics, companies are moving towards mathematical guarantees.

### A. Differential Privacy (DP)
Differential privacy mathematically guarantees that the presence or absence of a single individual in a dataset does not significantly change the outcome of any query run on that dataset.

*   **Mechanism**: It works by injecting calculated mathematical "noise" into query results.
*   **Pros**: Provides a strict mathematical "privacy budget" ($\epsilon$); mathematically immune to linkage attacks.
*   **Cons**: Extremely complex to configure; can degrade accuracy for small datasets.

### B. Synthetic Data
Using machine learning models (like GANs or LLMs) to generate completely artificial datasets that copy the statistical properties of real datasets without containing any real records.

*   **Pros**: Zero risk of direct re-identification.
*   **Cons**: Can lose rare correlations; models can memorize and accidentally regenerate real training samples.

---

## Legacy Anonymization Software & Libraries

When developers need to anonymize unstructured text files (PDFs, Word docs, texts), they traditionally turn to these open-source tools:

### ARX Data Anonymizer
A powerful, open-source Java application designed for structuring tabular data. It supports *k*-anonymity, *l*-diversity, *t*-closeness, and differential privacy.

*   *Limitation*: Built specifically for structured tables (CSV/databases). It cannot handle raw emails, PDFs, or conversational transcripts.

### Microsoft Presidio
A popular Python framework for detecting and redacting PII in unstructured text. It uses a combination of regular expressions (regexes) and classical Named Entity Recognition (NER) models (like Spacy or Hugging Face transformers).

*   *How it works*: Regexes look for patterns like emails, phone numbers, or credit card structures. The NER model tags entities like `PERSON`, `LOCATION`, and `DATE`.
*   *Limitation*: Classical NER models are sensitive to formatting, capitalization, and surrounding phrasing. They struggle when PII is implied rather than explicitly named. For example, in the sentence *"I'm sitting here with the author of the 'Harry Potter' series"*, Presidio might detect nothing, whereas an LLM knows "J.K. Rowling" is implied.

---

## Technical Comparison Table

| Technique | Data Type | Reversible? | High Utility? | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **Masking/Redaction** | Structured / Text | No | Low | Deleting direct identifiers in logs. |
| **Tokenization** | Structured | Yes (with DB) | High | Payment processors (PCI) & primary keys. |
| ***k*-Anonymity** | Tabular/Rows | No | Medium | Publicly releasing survey summaries. |
| **Differential Privacy** | Database Queries| No | High (Aggr) | Large-scale telemetry (e.g. Apple/Google). |
| **Legacy NER (Presidio)** | Text | No | Medium | Basic preprocessing & filtering. |
| **LLM-Based Masking** | Unstructured Text | Yes (with Map)| Very High | Complex documents, contracts, medical notes. |

---

**In this course:**  
[← Previous: History](history.md) | [Course Overview](index.md) | [Next: How PDF Anonymizer is Different](how-different.md)
