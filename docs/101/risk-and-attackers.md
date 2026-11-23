---
description: Prosecutor, journalist, and marketer risk models; WP29 legal criteria (singling out, linkability, inference); and machine-learning and LLM disclosure attacks.
---

# Lecture 4: Attacker Models and Disclosure Risk

Saying a dataset has "low re-identification risk" is meaningless until the **attacker's prior knowledge and objective** are specified. Statistical disclosure control (SDC), privacy law, and adversarial machine learning each formalize disclosure risk differently. This lecture connects all three.

---

## 1. The Three Classical SDC Attacker Models

Let $T$ be a released sample of $n$ records drawn from an underlying population $U$ of size $N \ge n$, partitioned by quasi-identifier columns $Q$ into equivalence classes $E_1, \dots, E_m$ in the sample (with corresponding population class sizes $F_1, \dots, F_m$ where $F_j \ge |E_j|$). Following Dankar and El Emam (2012), re-identification risk depends on what the adversary knows and seeks:[^dankar2012]

1. **Prosecutor model (membership known, targeted):** The adversary knows a specific target is in $T$ and knows their quasi-identifiers $Q$. If the target falls in equivalence class $E_j$, the re-identification probability is:

$$
r_{\text{pros}}(j) = \frac{1}{|E_j|}, \qquad R_{\text{pros}}^{\max} = \max_{j=1,\dots,m} \frac{1}{|E_j|}.
$$

Enforcing $k$-anonymity ($|E_j| \ge k$) bounds worst-case prosecutor risk by $1/k$.

2. **Journalist model (membership unknown, targeted):** The adversary does *not* know whether the target is in the sample $T$, only that the target belongs to the larger population $U$ (e.g., a state voter registry). Because other population members share the same quasi-identifiers outside $T$, the probability of correctly matching a record in $E_j$ to its population owner is bounded by the **population** class size $F_j$:

$$
r_{\text{journ}}(j) = \frac{1}{F_j} \le \frac{1}{|E_j|}.
$$

When $T$ is a full census ($T = U$), journalist risk equals prosecutor risk. When $T$ is a small random sample (sampling fraction $f = n/N \ll 1$), estimating $F_j$ requires population models (such as Poisson-gamma or log-linear estimation) rather than sample counts alone.

3. **Marketer model (bulk matching, untargeted):** The adversary attempts to match as many records in $T$ as possible against an external population list, caring about the **average** fraction of correctly linked records rather than a single worst-case outlier:

$$
R_{\text{mark}} = \frac{1}{n} \sum_{j=1}^{m} |E_j| \cdot \frac{1}{F_j}.
$$

When $T = U$ (so $F_j = |E_j|$), this simplifies to $R_{\text{mark}} = m / n$ — the number of equivalence classes divided by the number of records.

### Worked Example

Consider a full-population release ($T = U$, $n = 10$ records) partitioned into $m = 3$ equivalence classes of sizes $|E_1| = 2$, $|E_2| = 3$, and $|E_3| = 5$:

- **Maximum prosecutor (and journalist) risk:** $\max(1/2, 1/3, 1/5) = 0.50$.
- **Marketer (average) risk:** $m / n = 3 / 10 = 0.30$.

A single small equivalence class ($|E_1| = 2$) drives worst-case prosecutor risk to $50\%$ even when average marketer risk looks modest.

---

## 2. Regulatory Disclosure Criteria (WP29 / EDPB)

European data-protection guidance evaluates anonymization against three distinct operational failure modes rather than a single numeric threshold:[^wp29_2014]

| Criterion | Definition | Example |
|---|---|---|
| **Singling out** | Isolating some or all records that identify one individual in a dataset without necessarily knowing their name. | A unique record for a 98-year-old cardiologist in a small town. |
| **Linkability** | Linking two or more records concerning the same individual (within one dataset or across two datasets). | Matching a pseudonymized hospital release to a public news report by date and postal code. |
| **Inference** | Deducing, with significant probability, the value of an unknown sensitive attribute from other released attributes. | Learning a patient's diagnosis from a homogeneous $k$-anonymous group (violating $\ell$-diversity). |

A technique that mitigates singling out (such as $k$-anonymity) can still fail inference if sensitive attributes lack diversity.

---

## 3. Machine Learning and LLM Disclosure Attacks

When sensitive data enters a trained model or flows through narrative prose, three additional attacker models apply:

- **Membership inference:** Given black-box query access to a trained classifier or generative model and a candidate record $x$, an adversary determines whether $x$ was included in the training set by exploiting overfitting (higher model confidence or lower perplexity on training members).[^shokri2017]
- **Training-data extraction:** Prompting an autoregressive language model to emit memorized verbatim spans from its training corpus, including personal names, phone numbers, and email addresses.[^carlini2021]
- **Zero-shot attribute inference from pseudonymized text:** Even when explicit names and direct identifiers are removed from free text, frontier language models can infer latent personal attributes (location, age, occupation, gender, income) from subtle linguistic, cultural, and contextual clues at high accuracy and negligible cost.[^staab2024]

---

??? note "Exercises"
    1. **Risk calculation:** A clinic releases a full cohort table ($T = U$) of $n = 20$ patients across $m = 4$ equivalence classes of sizes $1, 4, 5, 10$. Compute (a) the worst-case prosecutor risk and (b) the marketer risk. Which single change most reduces prosecutor risk?
    2. **WP29 criteria:** Replacing every user's name with an unsalted `SHA-256` hash prevents casual visual reading. Which of the three WP29 criteria (*singling out*, *linkability*, *inference*) remain violated?

    ??? note "Solutions"
        1. (a) Worst-case prosecutor risk is $1 / \min(1, 4, 5, 10) = 1.0$ ($100\%$ for the unique record). (b) Marketer risk is $m / n = 4 / 20 = 0.20$. Generalizing or suppressing the size-1 outlier class (so $\min |E_j| \ge 4$) drops worst-case prosecutor risk from $1.0$ to $\le 0.25$.
        2. **All three remain at risk:** identical hashes preserve *linkability* across releases, unique rows allow *singling out*, and if the preimage space is small (e.g., emails or national IDs), dictionary reversal recovers the original identifier directly.

*Next lecture: [Lecture 5 — Document and File-Format Leakage](document-leakage.md).*

## References

[^dankar2012]: Dankar, F. K., & El Emam, K. (2012). *The Application of Differential Privacy to Health Data*. Proceedings of the 2012 Joint EDBT/ICDT Workshops, 158–166; and El Emam, K. (2013). *Guide to the De-Identification of Personal Health Information*. CRC Press.
[^wp29_2014]: Article 29 Data Protection Working Party (2014). *Opinion 05/2014 on Anonymisation Techniques* (WP 216).
[^shokri2017]: Shokri, R., Stronati, M., Song, C., & Shmatikov, V. (2017). *Membership Inference Attacks Against Machine Learning Models*. IEEE Symposium on Security and Privacy (S&P 2017), 3–18. <https://doi.org/10.1109/SP.2017.41>
[^carlini2021]: Carlini, N., Tramèr, F., Wallace, E., et al. (2021). *Extracting Training Data from Large Language Models*. USENIX Security 2021, 2633–2650. <https://www.usenix.org/conference/usenixsecurity21/presentation/carlini>
[^staab2024]: Staab, R., Vero, M., Balunović, M., & Vechev, M. (2024). *Beyond Memorization: Violating Privacy via Inference with Large Language Models*. ICLR 2024. <https://arxiv.org/abs/2310.07298>
