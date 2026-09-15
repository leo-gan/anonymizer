# Israel (`IL`)

National-ID patterns loaded when you pass `countries=["IL"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `ID_IL` — Teudat Zehut number

The 9-digit number on the Israeli identity card.

| | |
|---|---|
| **Package type** | `ID_IL` |
| **Shape this package looks for** | 9 digits |
| **Checksum** | none in this package (Luhn is official) |
| **Example (synthetic)** | `123456782` |

**Official sources**

- [Population and Immigration Authority — identity card](https://www.gov.il/en/departments/population_and_immigration_authority)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
