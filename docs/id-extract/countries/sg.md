# Singapore (`SG`)

National-ID patterns loaded when you pass `countries=["SG"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `NRIC_SG` — NRIC / FIN

The National Registration Identity Card number for citizens and PRs (prefix S, T) or the Foreign Identification Number (prefix F, G, M). This pattern covers S, G, and T.

| | |
|---|---|
| **Package type** | `NRIC_SG` |
| **Shape this package looks for** | S/G/T + 7 digits + letter |
| **Checksum** | none in this package |
| **Example (synthetic)** | `S1234567D` |

**Official sources**

- [ICA — NRIC](https://www.ica.gov.sg/documents/nric)
- [National Registration Act 1965](https://sso.agc.gov.sg/Act/NRA1965)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
