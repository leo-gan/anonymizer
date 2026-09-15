# Greece (`GR`)

National-ID patterns loaded when you pass `countries=["GR"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `AMKA_GR` — AMKA

The Greek social-security number (Αριθμός Μητρώου Κοινωνικής Ασφάλισης). Eleven digits.

| | |
|---|---|
| **Package type** | `AMKA_GR` |
| **Shape this package looks for** | 11 digits |
| **Checksum** | none |
| **Example (synthetic)** | `01018001234` |

**Official sources**

- [AMKA official site](https://www.amka.gr/)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
