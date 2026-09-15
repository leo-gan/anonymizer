# Argentina (`AR`)

National-ID patterns loaded when you pass `countries=["AR"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `DNI_AR` — DNI (Documento Nacional de Identidad)

The Argentine national identity number. RENAPER issues the document. This pattern is 8 digits only and will over-match.

| | |
|---|---|
| **Package type** | `DNI_AR` |
| **Shape this package looks for** | 8 digits |
| **Checksum** | none |
| **Example (synthetic)** | `12345678` |

**Official sources**

- [RENAPER / Mi Argentina — DNI](https://www.argentina.gob.ar/interior/renaper/dni)
- [Ley 17.671 (identificación, registro y clasificación del potencial humano nacional)](https://www.argentina.gob.ar/normativa/nacional/ley-17671-21708)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
