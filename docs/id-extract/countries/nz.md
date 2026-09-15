# New Zealand (`NZ`)

National-ID patterns loaded when you pass `countries=["NZ"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `IRD_NZ` — IRD number

Inland Revenue’s tax identifier for a person or entity. It is 8 or 9 digits, often written with hyphens.

| | |
|---|---|
| **Package type** | `IRD_NZ` |
| **Shape this package looks for** | 2–3 digits + 3–4 digits + 3 digits |
| **Checksum** | none in this package |
| **Example (synthetic)** | `490-918-50` |

**Official sources**

- [Inland Revenue — IRD numbers](https://www.ird.govt.nz/managing-my-tax/ird-numbers)
- [Tax Administration Act 1994](https://www.legislation.govt.nz/act/public/1994/0166/latest/DLM348343.html)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
