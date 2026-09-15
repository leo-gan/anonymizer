# Belgium (`BE`)

National-ID patterns loaded when you pass `countries=["BE"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `NISS_BE` — NISS / numéro de registre national

The Belgian national register number (also called NISS in social security). Eleven digits, often printed with dots and a hyphen.

| | |
|---|---|
| **Package type** | `NISS_BE` |
| **Shape this package looks for** | YY.MM.DD-NNN.CC or 11 digits |
| **Checksum** | none in this package |
| **Example (synthetic)** | `85.07.30-123.45` |

**Official sources**

- [FPS Interior — National Register](https://www.ibz.rrn.fgov.be/en/national-register/)
- [Crossroads Bank for Social Security — NISS](https://www.ksz-bcss.fgov.be/en)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
