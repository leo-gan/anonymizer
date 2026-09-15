# Finland (`FI`)

National-ID patterns loaded when you pass `countries=["FI"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `HETU_FI` — Henkilötunnus

The Finnish personal identity code. Date of birth, a century sign (+, -, or A), an individual number, and a check character.

| | |
|---|---|
| **Package type** | `HETU_FI` |
| **Shape this package looks for** | DDMMYY + +|-|A + 3 digits + alphanumeric |
| **Checksum** | none in this package |
| **Example (synthetic)** | `131052-308T` |

**Official sources**

- [Digital and Population Data Services Agency — personal identity code](https://dvv.fi/en/personal-identity-code)
- [Laki väestötietojärjestelmästä](https://www.finlex.fi/fi/laki/ajantasa/2009/20090661)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
