# South Africa (`ZA`)

National-ID patterns loaded when you pass `countries=["ZA"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `ID_ZA` — South African ID number

A 13-digit number on the green bar-coded ID or the smart ID card. The first six digits are the date of birth.

| | |
|---|---|
| **Package type** | `ID_ZA` |
| **Shape this package looks for** | 13 digits |
| **Checksum** | none in this package (Luhn is used officially) |
| **Example (synthetic)** | `8001015009087` |

**Official sources**

- [Department of Home Affairs — ID documents](https://www.dha.gov.za/index.php/civic-services/identity-documents)
- [Identification Act 68 of 1997](https://www.gov.za/documents/identification-act)

## `TAX_ZA` — SARS tax reference (structural)

A 10-digit token used as a coarse match for a SARS tax reference number.

| | |
|---|---|
| **Package type** | `TAX_ZA` |
| **Shape this package looks for** | 10 digits |
| **Checksum** | none |
| **Example (synthetic)** | `0123456789` |

**Official sources**

- [SARS — tax reference number](https://www.sars.gov.za/individuals/how-to-register-for-tax/)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
