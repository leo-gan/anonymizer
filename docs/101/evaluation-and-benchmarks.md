---
description: How to evaluate text anonymizers rigorously — mention vs. entity F1, direct vs. quasi-identifier weighting, residual leftover rates, utility loss, and public evaluation corpora.
---

# Lecture 7: Evaluation, Metrics, and Benchmarks

Unit tests confirm that a regex compiles or a mapping round-trips; they do **not** measure how many real identifiers leak on unseen documents. Evaluating text anonymization rigorously requires separating **detection accuracy**, **residual disclosure**, and **downstream utility**, and choosing benchmarks that reflect real-world difficulty.

---

## 1. Why Naive Token-Level $F_1$ Misleads

Standard NER benchmarks report aggregate micro-$F_1$ across all spans equally:

$$
\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}, \qquad
\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}, \qquad
F_1 = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}.
$$

In privacy engineering, a single aggregate $F_1$ hides three critical failure modes identified by the Text Anonymization Benchmark (TAB):[^pilan2022]

1. **Direct vs. quasi-identifier imbalance:** A document may contain 40 dates and organizations (quasi-identifiers) and 2 personal names (direct identifiers). Missing both names while catching 38 dates yields $90\%$ overall recall — yet the document is completely un-anonymized. Scores **must** be reported separately for direct and quasi-identifiers.
2. **Mention-level vs. entity-level recall:** Suppose `"Dr. Elena Rostova"` appears five times in a report and a system masks four occurrences while leaving the fifth in clear text. Mention-level recall is $80\%$, but **entity-level leakage is total** because one unmasked occurrence reveals the person's identity. Conversely, missing one quasi-identifier among several may not always isolate an individual.
3. **Asymmetric error cost (recall vs. precision):** False negatives (missed PII) create privacy breaches; false positives (over-redaction) degrade utility. While recall is prioritized for direct identifiers, unchecked false positives destroy usability — for example, an overly broad national driver-license regex (`\b[A-Z0-9]{5,15}\b`) rewrites uppercase section headings like `PROCEDURE` and `FACTS` across legal judgments.

---

## 2. Operational Leftover Rate and Utility Loss

Alongside span-level $F_1$, two complementary measurements capture operational behavior:

- **Leftover (residual) rate:** The fraction of gold mention strings that remain literally visible anywhere in the masked output text:

$$
\text{Leftover Rate} = \frac{\bigl|\{m \in G : \text{text}(m) \text{ appears in masked output}\}\bigr|}{|G|}.
$$

Splitting into **overall leftover** and **structured leftover** (emails, phones, cards, IBANs, SSNs) diagnoses whether leaks stem from deterministic pattern gaps or semantic/contextual misses.

- **Utility preservation:** Measuring what remains usable after masking — e.g., token retention ratio, readability, or downstream accuracy (question answering, classification, summarization) on masked vs. original text. Perfect $0\%$ leftover is trivial if a tool erases the entire document; evaluation always measures a **point on the privacy–utility curve**.

### Worked Calculation

Suppose a clinical note has 5 labeled gold spans: 2 mentions of one patient name (`"Ada Lovelace"`, `"Ada"` — both direct) and 3 quasi-identifiers (`"London"`, `"12 May 2024"`, `"cardiologist"`). A tool masks `"Ada Lovelace"`, `"London"`, and `"12 May 2024"`, misses `"Ada"` and `"cardiologist"`, and falsely masks the drug name `"Aspirin"`:

- **Mention counts:** $\text{TP} = 3$, $\text{FP} = 1$, $\text{FN} = 2$.
- **Mention metrics:** $\text{Precision} = 3/4 = 0.75$, $\text{Recall} = 3/5 = 0.60$, $F_1 = 2(0.75)(0.60)/(0.75+0.60) \approx 0.667$.
- **Split recall:** Direct recall $= 1/2 = 0.50$; Quasi recall $= 2/3 \approx 0.667$.
- **Leftover rate:** $2/5 = 40\%$ (`"Ada"` and `"cardiologist"` remain visible in the output).

---

## 3. Public Evaluation Corpora and the Synthetic Gap

| Corpus | Domain & Language | Annotation Granularity | Access / License | Key Limitation |
|---|---|---|---|---|
| **TAB**[^pilan2022] | ECHR court judgments (English) | Direct vs. quasi-identifier flags, entity clusters, masking decisions | Public (MIT) | Legal prose is dense with dates and demographic phrases. |
| **i2b2 / n2c2 2014**[^i2b2] | Clinical discharge summaries (English) | HIPAA PHI categories | Data-use agreement required | Restricted redistribution; U.S. hospital style. |
| **MIMIC-III / IV**[^mimic] | Critical-care EHRs (English) | Pre-de-identified clinical notes | PhysioNet credentialing + DUA | Cannot serve as raw-PII ground truth without synthetic re-injection. |
| **MAPA** | Legal & administrative (12 EU languages) | Multilingual entity tiers | Public (European Commission) | Narrower domain coverage. |
| **Presidio synthetic** | General synthetic text (English) | Structured PII + names | Public (MIT) | Synthetic templates are cleaner than real documents. |
| **Gretel PII Masking** | Multi-domain synthetic (English) | Broad entity types (5,000+ test docs) | Public (Apache-2.0) | Synthetic generation produces explicit, cleanly delimited entities. |

### Why Synthetic Benchmarks Overestimate Real-World Recall
Synthetic datasets insert cleanly formatted names and identifiers into short templates. Real documents contain coreferent pronouns, implicit roles, dense dates, OCR noise, and domain jargon. In empirical testing on 6,761 public documents ([Evaluation Results](../project/eval-results.md)), a hybrid RE2 + local 12B LLM pipeline achieved **$5.3\%$–$7.1\%$ leftover** on Gretel and Presidio synthetic documents, but **$56.4\%$ leftover** on real TAB court cases (driven primarily by unmasked dates and demographic quasi-identifiers rather than names). Reporting numbers solely on synthetic benchmarks therefore creates misleading confidence.

---

??? note "Exercises"
    1. **Direct vs. overall recall:** A document contains 20 labeled spans: 2 personal names (direct) and 18 dates/cities (quasi). System A catches 2/2 names and 12/18 quasi-identifiers. System B catches 0/2 names and 18/18 quasi-identifiers. Compare their overall recall and direct recall. Which system has higher privacy value?
    2. **Repeated mentions:** If `"John Smith"` occurs 3 times in a contract and a regex/NER system masks 2 occurrences while leaving 1 unmasked, why is mention recall ($66.7\%$) an overly optimistic summary of disclosure risk?

    ??? note "Solutions"
        1. System A has overall recall $14/20 = 70\%$ and **direct recall $100\%$**. System B has higher overall recall ($18/20 = 90\%$) but **direct recall $0\%$** — every person's name leaked in clear text. System A provides far stronger privacy protection despite a 20-point lower headline score.
        2. A single unmasked occurrence exposes `"John Smith"` verbatim across the contract (and if co-located with masked references, lets a reader infer the identity behind the other two placeholders as well). Entity-level complete-masking recall for that person is $0\%$.

*Next lecture: [Lecture 8 — Choosing a Method: Decision Framework](decision-framework.md).*

## References

[^pilan2022]: Pilán, I., Lison, P., Øvrelid, L., Papadopoulou, A., Sánchez, D., & Batet, M. (2022). *The Text Anonymization Benchmark (TAB): A Dedicated Corpus and Evaluation Framework for Text Anonymization*. Computational Linguistics, 48(4), 1053–1101. <https://doi.org/10.1162/coli_a_00458>
[^i2b2]: Stubbs, A., Kotfila, C., & Uzuner, Ö. (2015). *Automated Systems for the De-identification of Longitudinal Clinical Narratives: Overview of 2014 i2b2/UTHealth Shared Task Track 1*. Journal of Biomedical Informatics, 58, S11–S19. <https://doi.org/10.1016/j.jbi.2015.06.007>
[^mimic]: Johnson, A. E. W., Bulgarelli, L., Shen, L., et al. (2023). *MIMIC-IV, a freely accessible electronic health record dataset*. Scientific Data, 10, 1. <https://doi.org/10.1038/s41597-022-01899-x>
