# Canada (`CA`)

National-ID patterns loaded when you pass `countries=["CA"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `SIN_CA` — Social Insurance Number (SIN)

A unique 9-digit number issued by Service Canada. It identifies a person for income tax under Income Tax Act s. 237 and for certain federal programs. A personal SIN does not begin with 0 or 8. Temporary SINs begin with 9.

| | |
|---|---|
| **Package type** | `SIN_CA` |
| **Shape this package looks for** | NNN-NNN-NNN, first digit 1–7 or 9 |
| **Checksum** | Luhn |
| **Example (synthetic)** | `123-456-782` |

**Official sources**

- [Service Canada — Social Insurance Number](https://www.canada.ca/en/employment-social-development/services/sin.html)
- [CRA — SIN on a tax return](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/personal-address-information/social-insurance-number.html)
- [Income Tax Act (Canada)](https://laws-lois.justice.gc.ca/eng/acts/I-3.3/)

## `DRIVERS_LICENSE_CA` — Driver licence (province or territory)

Licences are issued by each province or territory. Formats vary. The second alternative in the pattern is very broad.

| | |
|---|---|
| **Package type** | `DRIVERS_LICENSE_CA` |
| **Shape this package looks for** | Letter + grouped digits, or 5–15 alphanumeric |
| **Checksum** | none |
| **Example (synthetic)** | `A1234-12345-12345` |

**Official sources**

- [Example issuer: Ontario — driver's licence](https://www.ontario.ca/page/drivers-licence)

## `PROGRAM_ACCOUNT_CA` — CRA program account

The business number plus a program identifier and a four-digit reference. The letters this package accepts are RT, RP, RC, RM, RZ, RR, and RG.

| | |
|---|---|
| **Package type** | `PROGRAM_ACCOUNT_CA` |
| **Shape this package looks for** | 9 digits + program letters + 4 digits |
| **Checksum** | none |
| **Example (synthetic)** | `123456789RT0001` |

**Official sources**

- [CRA — program accounts](https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/business-registration/business-number-program-account/need-program-accounts.html)

## `DIN_CA` — Drug Identification Number (DIN)

The eight-digit number Health Canada assigns to a drug before it is marketed. The label prints the prefix DIN. The match includes that prefix.

| | |
|---|---|
| **Package type** | `DIN_CA` |
| **Shape this package looks for** | DIN + 8 digits |
| **Checksum** | none |
| **Example (synthetic)** | `DIN 00000000` |

**Official sources**

- [Health Canada — DIN](https://www.canada.ca/en/health-canada/services/drugs-health-products/drug-products/fact-sheets/drug-identification-number.html)

## `NPN_CA` — Natural Product Number (NPN)

The eight-digit licence number on a natural health product. The match includes the prefix NPN.

| | |
|---|---|
| **Package type** | `NPN_CA` |
| **Shape this package looks for** | NPN + 8 digits |
| **Checksum** | none |
| **Example (synthetic)** | `NPN 00000000` |

**Official sources**

- [Health Canada — product licensing](https://www.canada.ca/en/health-canada/services/drugs-health-products/natural-non-prescription/applications-submissions/product-licensing.html)

## `DIN_HM_CA` — Homeopathic medicine number (DIN-HM)

The eight-digit number on a licensed homeopathic medicine. The match includes the prefix DIN-HM.

| | |
|---|---|
| **Package type** | `DIN_HM_CA` |
| **Shape this package looks for** | DIN-HM + 8 digits |
| **Checksum** | none |
| **Example (synthetic)** | `DIN-HM 00000000` |

**Official sources**

- [Health Canada — LNHPD terminology](https://www.canada.ca/en/health-canada/services/drugs-health-products/reports-publications/natural-health-products/licensed-natural-health-products-database-lnhpd-terminology-guide-september-2008.html)

## `UCI_CA` — Unique Client Identifier (UCI)

The client id IRCC prints on its documents. This package matches the 10-digit form NN-NNNN-NNNN. The 8-digit form is omitted because that hyphenation is too common.

| | |
|---|---|
| **Package type** | `UCI_CA` |
| **Shape this package looks for** | NN-NNNN-NNNN |
| **Checksum** | none |
| **Example (synthetic)** | `00-0000-0000` |

**Official sources**

- [IRCC — When will I get my UCI?](https://ircc.canada.ca/English/helpcentre/answer.asp?qnum=777&top=4)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
