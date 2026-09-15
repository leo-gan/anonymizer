# Portugal (`PT`)

National-ID patterns loaded when you pass `countries=["PT"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `NIF_PT` — NIF (Número de Identificação Fiscal)

The Portuguese tax identification number. Nine digits.

| | |
|---|---|
| **Package type** | `NIF_PT` |
| **Shape this package looks for** | 9 digits |
| **Checksum** | none in this package |
| **Example (synthetic)** | `123456789` |

**Official sources**

- [Autoridade Tributária — NIF](https://www.portaldasfinancas.gov.pt/at/html/index.html)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
