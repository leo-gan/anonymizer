# Thailand (`TH`)

National-ID patterns loaded when you pass `countries=["TH"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `NATIONAL_ID_TH` — Thai national ID number

A 13-digit number on the Thai national identity card. The first digit is never 0. The thirteenth digit is a check digit. A failed check is dropped, because thirteen digits are a common shape.

| | |
|---|---|
| **Package type** | `NATIONAL_ID_TH` |
| **Shape this package looks for** | 13 digits, first digit 1–9 |
| **Checksum** | Weights 13 through 2 on the first 12 digits. Check digit = (11 − sum mod 11) mod 10. A failure is dropped. |
| **Example (synthetic)** | `1101700200001` |

**Official sources**

- [Department of Provincial Administration — ID card](https://www.dopa.go.th/)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
