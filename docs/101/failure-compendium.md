---
description: Structured catalog of canonical real-world anonymization failures — quasi-identifier linkage, high-dimensional uniqueness, broken hashing, file-format leaks, and ML/LLM attacks.
---

# Compendium of Anonymization Failures

Empirical failures explain disclosure risk faster than abstract definitions. This compendium catalogs nine canonical real-world and peer-reviewed de-anonymization incidents grouped by root cause.

---

## 1. Quasi-Identifier Linkage

### Massachusetts GIC Medical Records (1997)
- **Attempted defense:** Removed direct identifiers (patient names, addresses, SSNs) from state-employee hospital visit records before research release.
- **Attack:** Latanya Sweeney purchased the Cambridge voter registration roll (USD 20) and joined the two tables on five-digit ZIP code, birth date, and sex, uniquely isolating Governor William Weld's medical record.[^sweeney2002] Subsequent census work estimated that $87\%$ of the U.S. population was uniquely identified by those three attributes alone.[^sweeney2000]
- **Lesson:** Demographic tuples act as unique keys; direct-identifier removal is never sufficient for tabular releases (motivating $k$-anonymity and HIPAA Safe Harbor).

### AOL Search Query Logs (2006)
- **Attempted defense:** Released 20 million web search queries from 650,000 users with usernames replaced by numeric IDs (e.g., `User 4417749`).
- **Attack:** Journalists read the longitudinal query stream of a single user ID — containing searches for local businesses, family surnames, and medical symptoms — and identified a 62-year-old resident of Lilburn, Georgia within days.[^aol2006]
- **Lesson:** Free-text behavioral histories contain embedded self-identifying clues that deterministic ID replacement cannot hide.

### Netflix Prize Dataset (2008)
- **Attempted defense:** Replaced subscriber identities with random numeric IDs across 100 million movie ratings and perturbed a subset of timestamps.
- **Attack:** Arvind Narayanan and Vitaly Shmatikov linked Netflix rating vectors to public IMDb review histories, showing that knowing just 6–8 rated titles and approximate dates uniquely identified subscribers in a 500,000-user dataset.[^narayanan2008]
- **Lesson:** Sparse, high-dimensional behavioral profiles act as fingerprints; syntactic grouping degrades rapidly as dimensionality grows.

---

## 2. High-Dimensional Uniqueness

### Mobile Phone Mobility Traces (2013)
- **Attempted defense:** Removed phone numbers and subscriber details from 15 months of coarse hourly cell-tower location logs covering 1.5 million individuals.
- **Attack:** Yves-Alexandre de Montjoye et al. demonstrated that just **four** spatiotemporal points (approximate time and antenna location) uniquely identified $95\%$ of individuals, and even coarsening spatial/temporal resolution only slowed uniqueness modestly.[^demontjoye2013]
- **Lesson:** Human trajectories are highly distinctive; coarse geographic and temporal binning often fails to achieve anonymity on longitudinal traces.

### Credit-Card Transaction Metadata (2015)
- **Attempted defense:** Released three months of card transactions for 1.1 million people with names, account numbers, and merchant addresses stripped — retaining only merchant ID, date, and transaction amount.
- **Attack:** de Montjoye et al. showed that **four** spatiotemporal purchase points uniquely re-identified $90\%$ of individuals, and adding approximate transaction prices raised uniqueness further.[^demontjoye2015]
- **Lesson:** Even purely numerical transaction metadata without names or text carries high re-identification risk.

---

## 3. Broken Cryptographic Masking

### New York City Taxi & Limousine Commission Logs (2014)
- **Attempted defense:** Released 173 million taxi trip records with driver hack licenses and cab medallion numbers masked using unsalted `MD5` hashes.
- **Attack:** Because valid NYC medallion and license formats spanned only a small, predictable keyspace (a few million combinations), researchers precomputed the `MD5` digest of every valid ID on commodity hardware and reversed the entire dataset in minutes — enabling linkage of celebrity pickup photos to driver identities, tips, and destinations.[^taxi2014]
- **Lesson:** Never use unsalted hashes (`MD5`, `SHA-256`) on low-entropy identifier domains; use keyed $\text{HMAC}_K$ or randomized stand-ins with separated key custody ([Lecture 6](pseudonymization-crypto.md)).

---

## 4. File-Format and ML / LLM Leakage

### PDF Overlay Redaction Failures (Recurring Public Court & Agency Leaks)
- **Attempted defense:** Authors drew opaque black rectangles over sensitive names and paragraphs in legal briefs and government filings (including high-profile federal court filings) and exported to PDF without excising underlying glyph objects.
- **Attack:** Readers selected text beneath the black rectangles, copied it into a text editor, or ran standard PDF text extraction to recover redacted passages verbatim.[^nsa2008]
- **Lesson:** Visual masking is not redaction. Digital PDFs require content-stream glyph excision, metadata/attachment stripping, and full non-incremental rewrite ([Lecture 5](document-leakage.md)).

### Verbatim Training-Data Extraction from LLMs (2021)
- **Attempted defense:** Assumed neural language models generalize statistically and do not expose individual personal records from web-scale training corpora.
- **Attack:** Nicholas Carlini et al. prompted GPT-2 to recover hundreds of verbatim memorized sequences, including full personal names, street addresses, phone numbers, and email addresses of real individuals.[^carlini2021]
- **Lesson:** Training models on unredacted text creates persistent memorization leakage; sensitive training data requires pre-training scrubbing, deduplication, and formal privacy bounds (such as DP-SGD).

### Zero-Shot Attribute Inference from Pseudonymized Prose (2024)
- **Attempted defense:** Removed explicit direct identifiers (names, usernames, contact details) from online posts and prose text.
- **Attack:** Robin Staab et al. showed that frontier LLMs accurately infer personal attributes — location, age, occupation, education, and income — purely from subtle linguistic and contextual cues in pseudonymized prose at a fraction of human investigator cost.[^staab2024]
- **Lesson:** Even perfect direct-identifier removal leaves indirect inference channels in narrative text; high-risk prose releases require indirect-identifier masking and human review.

---

## Summary Pattern

| Root Cause | Representative Incidents | Primary Countermeasure |
|---|---|---|
| **Quasi-identifier linkage** | GIC/Weld (1997), Netflix (2008), AOL (2006) | Syntactic generalization ($k$/$\ell$/$t$) or DP; indirect prose masking |
| **High-dimensional uniqueness** | Mobility (2013), Credit-card metadata (2015) | Aggregate DP releases rather than row-level microdata |
| **Unsalted low-entropy hashing** | NYC Taxi (2014) | Keyed $\text{HMAC}_K$, FF1 FPE, or randomized stand-ins |
| **Container / format residue** | PDF black-box overlays, Office metadata | Glyph excision, full rewrite, metadata/formula stripping |
| **Neural memorization & inference** | Carlini (2021), Staab (2024) | Scrubbing + DP-SGD for training; indirect-clue masking + access control |

## References

[^sweeney2002]: Sweeney, L. (2002). *$k$-Anonymity: A Model for Protecting Privacy*. IJUFKS, 10(5), 557–570. <https://doi.org/10.1142/S0218488502001648>
[^sweeney2000]: Sweeney, L. (2000). *Simple Demographics Often Identify People Uniquely*. CMU Data Privacy Lab Working Paper 3. <https://dataprivacylab.org/projects/identifiability/paper1.pdf>
[^aol2006]: Barbaro, M., & Zeller, T. Jr. (2006). *A Face Is Exposed for AOL Searcher No. 4417749*. The New York Times, August 9, 2006.
[^narayanan2008]: Narayanan, A., & Shmatikov, V. (2008). *Robust De-anonymization of Large Sparse Datasets*. IEEE S&P 2008, 111–125. <https://arxiv.org/abs/cs/0610105>
[^demontjoye2013]: de Montjoye, Y.-A., Hidalgo, C. A., Verleysen, M., & Blondel, V. D. (2013). *Unique in the Crowd: The privacy bounds of human mobility*. Scientific Reports, 3, 1376. <https://doi.org/10.1038/srep01376>
[^demontjoye2015]: de Montjoye, Y.-A., Radaelli, L., Singh, V. K., & Pentland, A. (2015). *Unique in the shopping mall: On the reidentifiability of credit card metadata*. Science, 347(6221), 536–539. <https://doi.org/10.1126/science.1256297>
[^taxi2014]: Pandurangan, V. (2014). *On Taxis and Rainbows: Lessons from NYC's Improperly Anonymized Taxi Logs*. <https://medium.com/@vijayp/of-taxis-and-rainbows-f6bc289679a1>
[^nsa2008]: National Security Agency (2008). *Redacting with Confidence: How to Safely Publish Sanitized Reports Converted from Word to PDF* (Report I333-015R-2005).
[^carlini2021]: Carlini, N., Tramèr, F., Wallace, E., et al. (2021). *Extracting Training Data from Large Language Models*. USENIX Security 2021, 2633–2650. <https://www.usenix.org/conference/usenixsecurity21/presentation/carlini>
[^staab2024]: Staab, R., Vero, M., Balunović, M., & Vechev, M. (2024). *Beyond Memorization: Violating Privacy via Inference with Large Language Models*. ICLR 2024. <https://arxiv.org/abs/2310.07298>
