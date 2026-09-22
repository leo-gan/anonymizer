# Singapore (`SG`)

National-ID patterns loaded when you pass `countries=["SG"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `NRIC_SG` — NRIC / FIN

The National Registration Identity Card number for citizens and permanent residents (prefix S or T) or the Foreign Identification Number (prefix F, G, or M). M is the FIN prefix issued from 2022.

| | |
|---|---|
| **Package type** | `NRIC_SG` |
| **Shape this package looks for** | S, T, F, G, or M + 7 digits + letter |
| **Checksum** | none in this package. ICA does not publish the check-letter algorithm. |
| **Example (synthetic)** | `S1234567D` |

**Official sources**

- [ICA — NRIC](https://www.ica.gov.sg/documents/nric)
- [National Registration Act 1965](https://sso.agc.gov.sg/Act/NRA1965)

## `UEN_SG` — Unique Entity Number (UEN)

The standard number for an entity registered in Singapore. Businesses registered before the current company form use eight digits and a letter. Local companies use nine digits and a letter, and the first four digits are the year of registration. Other entities use a T, S, or R, a two-digit year, a two-letter entity type, four digits, and a check letter. A failed check is dropped.

| | |
|---|---|
| **Package type** | `UEN_SG` |
| **Shape this package looks for** | 8 digits + letter, 9 digits + letter, or TSR + entity type + 4 digits + letter |
| **Checksum** | UEN check letter for each of the three forms. A local-company number whose year is in the future is rejected. A failure is dropped. |
| **Example (synthetic)** | `201912345R` |

**Official sources**

- [UEN](https://www.uen.gov.sg/)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
