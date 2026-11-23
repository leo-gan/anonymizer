---
description: Curated bibliography of technical standards (ISO/IEC 20889, NIST SP 800-188), foundational anonymization papers, public evaluation corpora, and open-source tools.
---

# Reading List, Standards, and Ecosystem

A curated directory of primary standards, peer-reviewed literature, evaluation corpora, and open-source tooling across the anonymization discipline.

---

## 1. Technical Standards and Regulatory Guidance

| Document | Issuing Body | Scope and Importance |
|---|---|---|
| **[ISO/IEC 20889:2018](https://www.iso.org/standard/69373.html)** | ISO / IEC | International taxonomy of de-identification terminology, mathematical privacy models, and technique classification. |
| **[NIST SP 800-188](https://csrc.nist.gov/pubs/sp/800/188/final)** (2023) | U.S. NIST | *De-Identifying Government Datasets* — practical engineering guidance on direct/quasi identifiers, re-identification risk assessment, and release governance. |
| **[NIST SP 800-38G](https://csrc.nist.gov/pubs/sp/800/38/g/final)** | U.S. NIST | *Methods for Format-Preserving Encryption* (FF1 specification and withdrawal of FF3-1). |
| **[GDPR Art. 4(5) & Recital 26](https://gdpr-info.eu/)** (2016/2018) | European Union | Binding legal distinction between pseudonymization (personal data) and irreversible anonymization (outside GDPR scope). |
| **WP29 Opinion 05/2014** (WP 216) | EU Article 29 Working Party | Operational evaluation of anonymization techniques against *singling out*, *linkability*, and *inference*. |
| **[EDPB Guidelines 01/2025](https://www.edpb.europa.eu/)** | European Data Protection Board | Detailed technical and organizational conditions for pseudonymization under GDPR. |
| **[HHS HIPAA De-identification Guidance](https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html)** (2012) | U.S. HHS | Operational rules for Safe Harbor (18 identifier classes) and Expert Determination under 45 CFR § 164.514. |

---

## 2. Foundational Research Papers

| Year | Authors | Paper | Contribution |
|---|---|---|---|
| 1972 | I. P. Fellegi | *On the Question of Statistical Confidentiality* ([JASA](https://doi.org/10.1080/01621459.1972.10481199)) | Formalized residual disclosure in published statistical tables. |
| 1977 | T. Dalenius | *Towards a Methodology for Statistical Disclosure Control* (Statistisk Tidskrift) | Stated the foundational confidentiality desideratum for statistical releases. |
| 1981 | D. Chaum | *Untraceable Electronic Mail, Return Addresses, and Digital Pseudonyms* ([CACM](https://doi.org/10.1145/358549.358563)) | Introduced mix networks and cryptographic unlinkability. |
| 1998 | P. Samarati & L. Sweeney | *Protecting Privacy when Disclosing Information* (SRI-CSL-98-04); Sweeney ([IJUFKS 2002](https://doi.org/10.1142/S0218488502001648)) | Formalized $k$-anonymity via generalization and suppression; Governor Weld linkage. |
| 2000 | L. Sweeney | *Simple Demographics Often Identify People Uniquely* ([CMU WP 3](https://dataprivacylab.org/projects/identifiability/paper1.pdf)) | Quantified population uniqueness of 5-digit ZIP, birth date, and sex in U.S. census data. |
| 2006 | A. Machanavajjhala et al. | *$\ell$-Diversity: Privacy Beyond $k$-Anonymity* ([ACM TKDD](https://doi.org/10.1145/1217299.1217302)) | Formalized attribute disclosure and homogeneity attacks on $k$-anonymous tables. |
| 2006 | C. Dwork et al. | *Calibrating Noise to Sensitivity in Private Data Analysis* ([TCC 2006](https://doi.org/10.1007/11681878_14)); Dwork & Roth (2014) | Introduced differential privacy and the Laplace mechanism. |
| 2007 | N. Li, T. Li, & S. Venkatasubramaniam | *$t$-Closeness: Privacy Beyond $k$-Anonymity and $\ell$-Diversity* ([ICDE 2007](https://doi.org/10.1109/ICDE.2007.367856)) | Bounded distributional distance of sensitive attributes per equivalence class. |
| 2008 | A. Narayanan & V. Shmatikov | *Robust De-anonymization of Large Sparse Datasets* ([arXiv](https://arxiv.org/abs/cs/0610105)) | Demonstrated high-dimensional linkage on the Netflix Prize dataset. |
| 2010 | P. Ohm | *Broken Promises of Privacy* (UCLA Law Review 57(6)) | Synthesized re-identification research for privacy law and regulatory policy. |
| 2013–15 | Y.-A. de Montjoye et al. | *Unique in the Crowd* ([Sci. Rep.](https://doi.org/10.1038/srep01376)); *Unique in the Shopping Mall* ([Science](https://doi.org/10.1126/science.1256297)) | Measured uniqueness bounds on human mobility and credit-card metadata. |
| 2017 | R. Shokri et al. | *Membership Inference Attacks Against Machine Learning Models* ([IEEE S&P](https://doi.org/10.1109/SP.2017.41)) | Formalized black-box membership inference against trained classifiers. |
| 2021 | N. Carlini et al. | *Extracting Training Data from Large Language Models* ([USENIX Security](https://www.usenix.org/conference/usenixsecurity21/presentation/carlini)) | Demonstrated verbatim PII extraction from autoregressive language models. |
| 2022 | I. Pilán et al. | *The Text Anonymization Benchmark (TAB)* ([Comp. Ling.](https://doi.org/10.1162/coli_a_00458)) | Defined direct/quasi evaluation methodology and open legal benchmark corpus. |
| 2024 | R. Staab et al. | *Beyond Memorization: Violating Privacy via Inference with LLMs* ([ICLR 2024](https://arxiv.org/abs/2310.07298)) | Quantified zero-shot personal attribute inference from pseudonymized text. |

---

## 3. Public Evaluation Corpora

| Corpus | Domain | Language | Access / License | Notes |
|---|---|---|---|---|
| **[TAB](https://github.com/NorskRegnesentral/text-anonymization-benchmark)** | ECHR court judgments | English | Public (MIT) | Gold standard for direct vs. quasi-identifier text evaluation. |
| **[i2b2 / n2c2 2014](https://portal.dbmi.hms.harvard.edu/)** | Clinical notes | English | Data-use agreement | Canonical HIPAA PHI clinical de-identification benchmark. |
| **[MIMIC-IV](https://physionet.org/content/mimiciv/)** | Critical-care EHRs | English | PhysioNet credentialing + DUA | Pre-de-identified clinical database (useful for utility/surrogate studies). |
| **[MAPA](https://mapa-project.eu/)** | Legal & administrative | 12 EU languages | Public (EC) | Multilingual hierarchical entity annotations. |
| **[Presidio Research](https://github.com/microsoft/presidio-research)** | General synthetic | English | Public (MIT) | Synthetic structured PII + names benchmark. |
| **[Gretel PII Masking v1](https://huggingface.co/datasets/gretelai/gretel-pii-masking-en-v1)** | Multi-domain synthetic | English | Public (Apache-2.0) | 5,000-document synthetic test split across broad entity types. |

---

## 4. Open-Source Tooling Ecosystem

A neutral map of mature open-source tools by workload class (see [Lecture 8: Decision Framework](decision-framework.md) for selection guidance):

| Class | Tools | Primary Strength |
|---|---|---|
| **Tabular syntactic SDC** | [ARX Data Anonymizer](https://arx.deidentifier.org/), [sdcMicro](https://cran.r-project.org/package=sdcMicro) | Full $k$-anonymity, $\ell$-diversity, $t$-closeness, prosecutor/journalist/marketer risk analysis on microdata tables. |
| **Differential privacy** | [OpenDP](https://opendp.org/), [Tumult Analytics](https://www.tmlt.dev/), [Google DP](https://github.com/google/differential-privacy) | Formal $(\varepsilon, \delta)$-DP aggregate queries, SQL analytics, and privacy-budget accounting. |
| **DP machine learning** | [Opacus](https://opacus.ai/) (PyTorch), [JAX Privacy](https://github.com/google-deepmind/jax_privacy) | Differentially private stochastic gradient descent (DP-SGD) for neural network training. |
| **Rule & classical NER** | [Microsoft Presidio](https://microsoft.github.io/presidio/), [Philter](https://github.com/BCHSI/philter-ucsf) | Modular regex + spaCy/transformer PII detection and clinical redaction pipelines. |
| **Metadata scrubbing** | [MAT2](https://0xacab.org/jvoisin/mat2) | Removing embedded file metadata across PDFs, images, audio, and office archives. |
| **Hybrid document pseudonymization** | `pdf-anonymizer` & `id-extract` (this repo) | Reversible span-based pseudonymization across PDF/DOCX/CSV/XLSX with RE2 + checksums, local GLiNER/Ollama, indirect-clue detection, and encrypted mappings. |
