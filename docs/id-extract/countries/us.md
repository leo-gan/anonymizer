# United States (`US`)

National-ID patterns loaded when you pass `countries=["US"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `SSN_US` — Social Security number (SSN)

A nine-digit number assigned by the Social Security Administration to record earnings and administer benefits. It is also used as a taxpayer identifier.

| | |
|---|---|
| **Package type** | `SSN_US` |
| **Shape this package looks for** | AAA-GG-SSSS |
| **Checksum** | none |
| **Example (synthetic)** | `123-45-6789` |

**Official sources**

- [SSA — request a Social Security number](https://www.ssa.gov/number-card/request-number-first-time)
- [SSA POMS RM 10201.030 — structure of the SSN](https://secure.ssa.gov/poms.nsf/lnx/0110201030)
- [Social Security Act](https://www.ssa.gov/OP_Home/ssact/ssact.htm)

## `SSN` — SSN (legacy key)

Same pattern as SSN_US. Kept so older callers that ask for type SSN still match.

| | |
|---|---|
| **Package type** | `SSN` |
| **Shape this package looks for** | AAA-GG-SSSS |
| **Checksum** | none |
| **Example (synthetic)** | `123-45-6789` |

**Official sources**

- [SSA — Social Security numbers](https://www.ssa.gov/ssnumber/)

## `EIN_US` — Employer Identification Number (EIN)

A nine-digit federal tax identifier the IRS assigns to businesses, estates, trusts, and other entities. Form SS-4 is the application.

| | |
|---|---|
| **Package type** | `EIN_US` |
| **Shape this package looks for** | NN-NNNNNNN |
| **Checksum** | none |
| **Example (synthetic)** | `12-3456789` |

**Official sources**

- [IRS — Employer identification number](https://www.irs.gov/businesses/employer-identification-number)
- [About Form SS-4](https://www.irs.gov/forms-pubs/about-form-ss-4)

## `MEDICAL_NPI_US` — National Provider Identifier (NPI)

A 10-digit identifier for covered health-care providers under HIPAA Administrative Simplification. CMS assigns it through NPPES. The number is intelligence-free.

| | |
|---|---|
| **Package type** | `MEDICAL_NPI_US` |
| **Shape this package looks for** | 10 digits |
| **Checksum** | Luhn over prefix 80840 + the 10 digits (CMS) |
| **Example (synthetic)** | `1234567893` |

**Official sources**

- [CMS — National Provider Identifier Standard](https://www.cms.gov/regulations-and-guidance/administrative-simplification/nationalprovidentstand)
- [45 CFR Part 162 (HIPAA unique identifiers)](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-162)

## `DRIVERS_LICENSE_US` — Driver licence (state)

Each U.S. state issues its own licence. There is no single federal format. This pattern is deliberately broad.

| | |
|---|---|
| **Package type** | `DRIVERS_LICENSE_US` |
| **Shape this package looks for** | 1–2 letters + 6–8 digits, or 8–9 digits, or 1 letter + 7–8 digits |
| **Checksum** | none |
| **Example (synthetic)** | `D1234567` |

**Official sources**

- [AAMVA — driver licensing](https://www.aamva.org/topics/driver-licensing)

## `MEDICAL_LICENSE_US` — Medical or DEA-style licence (structural)

A coarse pattern for U.S. professional or DEA-style licence tokens. It is not a complete DEA or state-board recognizer.

| | |
|---|---|
| **Package type** | `MEDICAL_LICENSE_US` |
| **Shape this package looks for** | 1–2 letters + 6–9 digits |
| **Checksum** | none |
| **Example (synthetic)** | `AB1234567` |

**Official sources**

- [DEA — registration](https://www.deadiversion.usdoj.gov/drugreg/index.html)

## `ITIN_US` — Individual Taxpayer Identification Number (ITIN)

A tax processing number for a person who needs a U.S. taxpayer identifier and cannot get an SSN. It uses the SSN hyphenation, starts with 9, and the fourth and fifth digits fall in the IRS ranges. A same-span SSN label is dropped.

| | |
|---|---|
| **Package type** | `ITIN_US` |
| **Shape this package looks for** | 9NN-NN-NNNN, middle digits 50–65, 70–88, 90–92, or 94–99 |
| **Checksum** | none |
| **Example (synthetic)** | `900-70-0000` |

**Official sources**

- [IRS — Taxpayer identification numbers](https://www.irs.gov/tin/taxpayer-identification-numbers-tin)
- [IRM 3.21.263 — ITIN ranges](https://www.irs.gov/irm/part3/irm_03-021-263r)

## `ATIN_US` — Adoption Taxpayer Identification Number (ATIN)

A temporary IRS number for a child in a pending domestic adoption. It uses the SSN hyphenation, starts with 9, and the fourth and fifth digits are 93.

| | |
|---|---|
| **Package type** | `ATIN_US` |
| **Shape this package looks for** | 9NN-93-NNNN |
| **Checksum** | none |
| **Example (synthetic)** | `900-93-0000` |

**Official sources**

- [IRM 3.13.40 — ATIN format](https://www.irs.gov/irm/part3/irm_03-013-040)

## `PTIN_US` — Preparer Tax Identification Number (PTIN)

The identifier a paid tax return preparer puts on returns they prepare. The IRS describes it as the letter P followed by eight digits.

| | |
|---|---|
| **Package type** | `PTIN_US` |
| **Shape this package looks for** | P + 8 digits |
| **Checksum** | none |
| **Example (synthetic)** | `P00000000` |

**Official sources**

- [IRM 3.12.2 — PTIN](https://www.irs.gov/irm/part3/irm_03-012-002r)

## `MBI_US` — Medicare Beneficiary Identifier (MBI)

The 11-character identifier CMS prints on Medicare cards. Characters 2, 5, 8, and 9 are letters. Letters S, L, O, I, B, and Z are excluded. Dashes on the card are optional in text.

| | |
|---|---|
| **Package type** | `MBI_US` |
| **Shape this package looks for** | 11 characters, CMS position classes, optional dashes as 4-3-4 |
| **Checksum** | none |
| **Example (synthetic)** | `1EG4-TE5-MK73` |

**Official sources**

- [CMS — MBI format](https://www.cms.gov/medicare/new-medicare-card/understanding-the-mbi-with-format.pdf)

## `A_NUMBER_US` — Alien Registration Number

The DHS file number for a non-citizen. USCIS describes it as the letter A followed by 7, 8, or 9 digits. A shorter number is padded with zeros in current systems.

| | |
|---|---|
| **Package type** | `A_NUMBER_US` |
| **Shape this package looks for** | A, optional hyphen, 7–9 digits |
| **Checksum** | none |
| **Example (synthetic)** | `A000000001` |

**Official sources**

- [USCIS — A-Number](https://www.uscis.gov/glossary-term/50684)

## `USCIS_RECEIPT_US` — USCIS receipt number

The 13-character identifier USCIS assigns to an application or petition: three letters and ten digits.

| | |
|---|---|
| **Package type** | `USCIS_RECEIPT_US` |
| **Shape this package looks for** | 3 letters + 10 digits |
| **Checksum** | none |
| **Example (synthetic)** | `ABC0000000001` |

**Official sources**

- [USCIS — receipt number field](https://my.uscis.gov/accounts/annual-asylum-fee/questionnaire)

## `DOS_CASE_US` — Department of State immigrant case ID

The case id on an immigrant visa packet. USCIS describes the ordinary form as three letters and 9 or 10 digits, and a Diversity Visa case as four digits, two letters, and five digits. A same-span USCIS receipt wins.

| | |
|---|---|
| **Package type** | `DOS_CASE_US` |
| **Shape this package looks for** | 3 letters + 9 or 10 digits, or 4 digits + 2 letters + 5 digits |
| **Checksum** | none |
| **Example (synthetic)** | `XYZ0123456789` |

**Official sources**

- [USCIS — A-Number and DOS case ID](https://www.uscis.gov/forms/filing-fees/uscis-immigrant-fee/immigrant-fee-payment-tips-on-finding-your-a-number-and-dos-case-id)

## `DEA_US` — DEA registration number

The controlled-substance registration number: two letters and seven digits. A hospital may append a hyphen and an internal suffix under 21 CFR 1301.22(c). A same-span medical-licence label is dropped.

| | |
|---|---|
| **Package type** | `DEA_US` |
| **Shape this package looks for** | 2 letters + 7 digits, optional hyphen and suffix |
| **Checksum** | none |
| **Example (synthetic)** | `AB1234567` |

**Official sources**

- [DEA Practitioner's Manual](https://www.deadiversion.usdoj.gov/GDP/%28DEA-DC-071%29%28EO-DEA226%29_Practitioner%27s_Manual_%28final%29.pdf)
- [21 CFR 1301.22](https://www.ecfr.gov/current/title-21/chapter-II/part-1301/section-1301.22)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
