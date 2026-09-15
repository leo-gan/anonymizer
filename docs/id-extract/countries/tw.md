# Taiwan (`TW`)

National-ID patterns loaded when you pass `countries=["TW"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `NATIONAL_ID_TW` — National ID number (身分證字號)

A 10-character number: one letter (place of registration) plus 9 digits.

| | |
|---|---|
| **Package type** | `NATIONAL_ID_TW` |
| **Shape this package looks for** | 1 letter + 9 digits |
| **Checksum** | none in this package |
| **Example (synthetic)** | `A123456789` |

**Official sources**

- [Ministry of the Interior — household registration](https://www.ris.gov.tw/app/en)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
