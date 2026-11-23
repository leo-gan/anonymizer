# Lecture 3: Formal Models and Methods

Privacy-preserving transformations fall into four families depending on data structure (tabular vs. unstructured text) and whether the guarantee is operational, syntactic, or probabilistic. This lecture defines each family formally and summarizes how unstructured text systems are evaluated.

---

## 1. Deterministic and Structural Transforms

Applied to individual fields or detected spans without modeling population distributions:

- **Redaction and masking:** Permanently removing or partially obscuring characters (e.g., `****-****-****-1111`). Irreversible; low downstream linkability.
- **Generalization and perturbation:** Coarsening precision (exact date $\to$ year, five-digit ZIP $\to$ three-digit prefix, exact age $\to$ age band) or shifting values by an offset. Many-to-one transforms are generally irreversible.
- **Hashing and keyed tokenization:** Mapping values through a cryptographic digest $H(x)$ or keyed function $\text{HMAC}_K(x)$. Unsalted hashes over small domains (such as ZIP codes or SSNs) are vulnerable to brute-force dictionary reversal.
- **Reversible pseudonymization:** Replacing each entity with a typed stand-in (`PERSON_1`, `EMAIL_1`) while storing the bijective mapping table separately, optionally encrypted. Preserves referential integrity within a document or corpus; security depends entirely on protecting the mapping.

---

## 2. Syntactic Privacy Models for Microdata Tables

Let a microdata table $T$ consist of records partitioned into equivalence classes $E_1, \dots, E_m$ that share identical values across a declared set of quasi-identifier columns $Q$, and let $S$ denote a sensitive attribute (e.g., diagnosis).

### $k$-Anonymity
A release $T$ satisfies **$k$-anonymity** with respect to $Q$ if every equivalence class contains at least $k$ records:[^samarati1998]

$$
\forall E \in \{E_1, \dots, E_m\}, \quad |E| \ge k.
$$

Under the *prosecutor* attacker model (the adversary knows the target is in $T$ and knows their quasi-identifiers $Q$), the probability of uniquely linking a target to a specific row is bounded by $1 / |E| \le 1 / k$. Enforcement relies on **generalization** (coarsening column values) and **suppression** (replacing outlier cells or rows with `*`).

### $\ell$-Diversity
$k$-Anonymity prevents record linkage but not **attribute disclosure**. If every record in an equivalence class shares the same sensitive value (a *homogeneity attack*), an adversary learns $S$ without needing to distinguish individual rows. A table satisfies **distinct $\ell$-diversity** if every equivalence class contains at least $\ell$ distinct values of $S$ (with stronger entropy and recursive variants also defined in the literature):[^machanavajjhala2006]

$$
\forall E, \quad \bigl|\{r[S] : r \in E\}\bigr| \ge \ell.
$$

### $t$-Closeness
Even when an equivalence class is $\ell$-diverse, skewness or semantic similarity among values can still leak information. A table satisfies **$t$-closeness** if, for every equivalence class $E$, the statistical distance $D(P_E, P_T)$ (typically Earth Mover's Distance) between the distribution $P_E$ of $S$ in $E$ and the global distribution $P_T$ across $T$ is at most $t$:[^li2007]

$$
\forall E, \quad D(P_E, P_T) \le t.
$$

### Worked Example

Consider a 4-row clinical table with $Q = \{\text{ZIP}, \text{Age}\}$ and $S = \text{Diagnosis}$ after generalizing to 2-anonymity:

| Equivalence Class | ZIP | Age | Diagnosis ($S$) |
|---|---|---|---|
| $E_1$ | `021**` | `30–39` | Influenza |
| $E_1$ | `021**` | `30–39` | Influenza |
| $E_2$ | `021**` | `40–49` | Asthma |
| $E_2$ | `021**` | `40–49` | Migraine |

- Every class has $|E_i| = 2$, so the table satisfies **$2$-anonymity** (prosecutor linkage risk $\le 0.5$).
- Class $E_1$ has only one distinct diagnosis (`Influenza`), so the table **violates $2$-diversity**: knowing a patient is in `021**` and aged 30–39 discloses their diagnosis with certainty.

---

## 3. Semantic and Generative Models

### Differential Privacy
Rather than constraining the released table directly, **differential privacy** bounds the influence of any single individual on the output distribution of a randomized mechanism $\mathcal{M}$.[^dwork2006] Mechanism $\mathcal{M}$ satisfies $(\varepsilon, \delta)$-differential privacy if, for all neighboring datasets $D, D'$ differing in at most one individual's record and all measurable subsets $S$ of outputs:

$$
\Pr\bigl[\mathcal{M}(D) \in S\bigr] \le e^{\varepsilon}\,\Pr\bigl[\mathcal{M}(D') \in S\bigr] + \delta.
$$

The parameter $\varepsilon > 0$ is the **privacy budget** (smaller $\varepsilon$ means stronger indistinguishability, typically requiring larger calibrated noise such as Laplace or Gaussian perturbation); $\delta \ge 0$ permits a negligible failure probability ($\delta = 0$ gives pure $\varepsilon$-DP). Unlike syntactic models, differential privacy resists arbitrary auxiliary knowledge and composes mathematically across repeated queries, but it applies naturally to aggregate statistics and ML training rather than verbatim reversible document editing.

### Synthetic Data
Generative models trained on private records synthesize artificial datasets that approximate the joint distribution of the source without copying real rows. Synthetic data does not automatically guarantee privacy unless trained with a formal mechanism such as DP-SGD, because overfitted models can reproduce training records verbatim.

---

## 4. Unstructured Text De-identification and Evaluation

Narrative documents (PDFs, clinical notes, legal filings) lack fixed schemas. Practical text de-identification systems combine three layers of detection:

1. **Deterministic patterns and checksums:** Linear-time regular expressions (RE2) paired with algorithmic validators (Luhn for payment cards, ISO 13616 mod-97 for IBAN, national ID check digits). High precision on structured strings; blind to names and prose context.
2. **Classical and span NER:** Sequence taggers (e.g., spaCy, Microsoft Presidio) and zero-shot span extractors (e.g., GLiNER) detect named entities (`PERSON`, `ORGANIZATION`, `LOCATION`, `DATE`) locally. Sensitive to phrasing and generally unable to detect indirect descriptions without explicit names.
3. **Contextual LLM detection:** Instruction-tuned language models detect coreferent variations and indirect identifying descriptions (e.g., *"the CEO of Tesla in Austin"*), at higher compute cost and with non-deterministic variance.

### Evaluation Metrics (TAB Framework)
Following the Text Anonymization Benchmark (Pilán et al., 2022), text systems are evaluated on labeled gold spans using **precision**, **recall**, and **$F_1$**, reported separately for **direct identifiers** and **quasi-identifiers** (and at both mention and entity levels):[^pilan2022]

$$
\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}, \qquad
\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}, \qquad
F_1 = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}.
$$

Separating direct from quasi-identifiers prevents high recall on frequent locations or organizations from obscuring missed personal names. In operational audits, recall is complemented by **leftover rate** — the fraction of gold mention strings still visible in clear text after masking.

---

## 5. Summary Comparison

| Method / Tool Class | Data Structure | Formal Guarantee | Reversible? | Representative Tools / Uses |
|---|---|---|---|---|
| **Redaction / Masking** | Structured or text | None (heuristic) | No | Log scrubbing, permanent black-box redaction |
| **Reversible Pseudonymization** | Text, tables, records | None alone (depends on key control) | Yes (with mapping) | External AI workflows, longitudinal linkage |
| **$k$-Anonymity / $\ell$-Diversity / $t$-Closeness** | Tabular microdata | Syntactic (given $Q$) | No | ARX Data Anonymizer; clinical/survey table releases |
| **Differential Privacy** | Aggregate queries, ML | Semantic $(\varepsilon, \delta)$ | No | National censuses, telemetry, DP-SGD training |
| **Rule + Classical NER** | Unstructured text | Empirical (recall/precision) | Rarely | Microsoft Presidio, spaCy pipelines |
| **Hybrid Regex + NER / LLM** | Unstructured text & tables | Empirical (benchmark + residual scan) | Yes (with mapping) | `pdf-anonymizer` (Case Study in Lecture 4) |

---

*Next lecture: [Lecture 4 — Unstructured Text Case Study](how-different.md).*

## References

[^samarati1998]: Samarati, P., & Sweeney, L. (1998). *Protecting Privacy when Disclosing Information: $k$-Anonymity and Its Enforcement through Generalization and Suppression*. Technical Report SRI-CSL-98-04, SRI International.
[^machanavajjhala2006]: Machanavajjhala, A., Gehrke, J., Kifer, D., & Venkitasubramaniam, M. (2006). *$\ell$-Diversity: Privacy Beyond $k$-Anonymity*. IEEE ICDE 2006; ACM TKDD, 1(1), 2007.
[^li2007]: Li, N., Li, T., & Venkatasubramaniam, S. (2007). *$t$-Closeness: Privacy Beyond $k$-Anonymity and $\ell$-Diversity*. IEEE ICDE 2007, 106–115.
[^dwork2006]: Dwork, C., McSherry, F., Nissim, K., & Smith, A. (2006). *Calibrating Noise to Sensitivity in Private Data Analysis*. TCC 2006, LNCS 3876, 265–284; and Dwork, C., & Roth, A. (2014). *The Algorithmic Foundations of Differential Privacy*. Foundations and Trends in Theoretical Computer Science, 9(3–4), 211–407.
[^pilan2022]: Pilán, I., Lison, P., Øvrelid, L., Papadopoulou, A., Sánchez, D., & Batet, M. (2022). *The Text Anonymization Benchmark (TAB): A Dedicated Corpus and Evaluation Framework for Text Anonymization*. Computational Linguistics, 48(4), 1053–1101.
