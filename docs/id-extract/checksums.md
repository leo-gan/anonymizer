---
description: Mathematical overview of check-digit algorithms (Luhn, ISO 13616 mod-97, Verhoeff, weighted modular sums) and why checksums govern precision vs. recall in PII detection.
---

# Identifier Syntax and Check-Digit Algorithms

Regular expressions match only **lexical shape** — digit counts, prefixes, and delimiters. In free text, shapes alone collide frequently with order numbers, timestamps, section headings, and serial codes. Because regular-expression engines like RE2 cannot compute arithmetic check digits, `id-extract` pairs linear-time syntax matching with a second deterministic **checksum validation** stage (`id_extract/checksums.py`).

---

## 1. Major Check-Digit Families

National and payment identifiers typically embed one or two redundant check digits designed to catch transcription errors (single-digit substitutions and adjacent transpositions):

| Algorithm | Mathematical Mechanism | Error Detection | Example Identifiers in `id-extract` |
|---|---|---|---|
| **Luhn (Mod-10)** (ISO/IEC 7812) | Alternately doubles digits from right to left, subtracts 9 if $> 9$, and requires total $\equiv 0 \pmod{10}$. | All single-digit errors; most adjacent transpositions (misses `09` $\leftrightarrow$ `90`). | `CREDIT_CARD`, `SIN_CA`, `MEDICAL_NPI_US` (prefixed with `80840`) |
| **ISO 13616 Mod-97** (ISO/IEC 7064) | Moves the 4-character country+check prefix to the end, expands letters `A`–`Z` $\to 10$–$35$, and checks $\text{int} \equiv 1 \pmod{97}$ plus country-specific length. | Single-digit, double-digit, and adjacent transposition errors ($\approx 99\%$ random rejection). | `IBAN` (validates against 75+ official country lengths) |
| **Verhoeff (Dihedral $D_5$)** | Multiplies digits via the non-commutative dihedral group $D_5$ permutation table rather than modular arithmetic. | All single-digit substitutions and **all** adjacent transpositions. | `AADHAAR_IN` |
| **Weighted Mod-10 / Mod-11 / Mod-23** | Computes $\sum w_i d_i \pmod{m}$ with fixed position weights $w_i$ and compares against check digit(s) or check letter. | Single-digit and transposition errors (stronger when modulus $m$ is prime, e.g., $11$ or $23$). | `VIN` (ISO 3779 mod-11), `DNI_ES` / `NIE_ES` (mod-23), `RESIDENT_ID_CN` (mod-11), `CPF_BR` (two mod-11 digits), `PESEL_PL`, `RTN_US` (`3,7,1`), `CLABE_MX`, `NHS_GB` (mod-11), `STEUER_ID_DE`, `NATIONAL_ID_TH`, `NATIONAL_ID_TR`, `ACN_AU`, `MEDICARE_AU`, `PHN_BC_CA`, `DEA_US`, `PERSONALAUSWEIS_DE` (ICAO 9303), `CUSIP_NNA`, `CODICE_FISCALE_IT`, `UEN_SG`, `HETU_FI` |

---

## 2. Why Unchecksummed Patterns Cause Precision Collapse

Many widely issued identifiers — including U.S. Social Security numbers (`SSN_US`), U.S. EINs, and most national driver licenses — **have no mathematical check digit**. Their regexes rely solely on format rules (such as excluded SSN area `000`/`666` or hyphenation).

When a national format is short or alphanumeric without fixed punctuation, precision degrades sharply on prose:

- In the 0.31.0 benchmark ([Evaluation Results](../project/eval-results.md#why-the-legal-number-is-not-a-name-leak)), a former Canadian driver-license catch-all (`\b[A-Z0-9]{5,15}\b`) fired 1,459 times across 254 European court judgments, rewriting uppercase headings such as `PROCEDURE` and `FACTS` into `DRIVERS_LICENSE_CA`. Tightening `DRIVERS_LICENSE_CA` (and the equivalent `AU`/`DE`/`ES`/`FR`/`IT` patterns) to require digits eliminated all 2,055 false-positive driver-license hits on those 254 judgments.
- Narrowing country scope via `countries=["US", "GB"]` (CLI: `--countries US,GB`) and keeping broad state/provincial patterns opt-in (`opt_in=`) prevents unrelated national syntaxes from polluting precision.

---

## 3. Failed Checksums: `TYPE_LIKE` vs. Strict Drop

In privacy detection, a checksum failure has two opposite interpretations:

1. **Mistyped real identifier (high privacy risk):** A human transcribed an IBAN or credit card with one wrong digit. Dropping the hit leaves 15 real card digits or 21 real IBAN characters visible in clear text.
2. **Coincidental bare digit run (high noise risk):** An 9- or 10-digit order number or timestamp happens to match the length of an ABA routing number (`RTN_US`) or UK NHS number (`NHS_GB`).

`id-extract` handles the 26 validated types in `checksums.py` with a two-tier policy:

| Policy | Score | Behavior on Failed Checksum | Types in `id-extract` |
|---|---|---|---|
| **Keep as `TYPE_LIKE`** (15 types) | `0.55` | Retain span and append `_LIKE` (e.g., `IBAN_LIKE`, `CREDIT_CARD_LIKE`). Hidden by default; filterable via `--min-confidence`. | `CREDIT_CARD`, `IBAN`, `VIN`, `MEDICAL_NPI_US`, `SIN_CA`, `DNI_ES`, `NIE_ES`, `RESIDENT_ID_CN`, `AADHAAR_IN`, `CPF_BR`, `CODICE_FISCALE_IT`, `PESEL_PL`, `DEA_US`, `PERSONALAUSWEIS_DE`, `HETU_FI` |
| **Strict drop** (11 types) | — | Drop failed matches completely because the bare digit or alphanumeric run is too common in ordinary text. | `RTN_US`, `CUSIP_NNA`, `PHN_BC_CA`, `CLABE_MX`, `ACN_AU`, `MEDICARE_AU`, `NHS_GB`, `UEN_SG`, `NATIONAL_ID_TH`, `NATIONAL_ID_TR`, `STEUER_ID_DE` |

Verified hits receive score `0.95`; unchecksummed pattern matches receive `0.85`. See [Install and API](api.md) and [Recognizer, Source, and Score](../project/terminology.md#recognizer-source-and-score).
