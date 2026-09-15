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

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
