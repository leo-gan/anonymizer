# Hong Kong (`HK`)

National-ID patterns loaded when you pass `countries=["HK"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `HKID_HK` — Hong Kong Identity Card number

The number on the HKID. One or two letters, six digits, and a check digit in parentheses in print (here the last character is the check).

| | |
|---|---|
| **Package type** | `HKID_HK` |
| **Shape this package looks for** | 1–2 letters + 6 digits + 0–9 or A |
| **Checksum** | none in this package |
| **Example (synthetic)** | `A1234563` |

**Official sources**

- [Immigration Department — HKID](https://www.immd.gov.hk/eng/services/hkid.html)
- [Registration of Persons Ordinance (Cap. 177)](https://www.elegislation.gov.hk/hk/cap177)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
