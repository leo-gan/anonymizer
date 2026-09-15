# Denmark (`DK`)

National-ID patterns loaded when you pass `countries=["DK"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `CPR_DK` — CPR-nummer

The Danish civil-registration number. Ten digits with a hyphen: DDMMYY-XXXX.

| | |
|---|---|
| **Package type** | `CPR_DK` |
| **Shape this package looks for** | 6 digits + hyphen + 4 digits |
| **Checksum** | none |
| **Example (synthetic)** | `010180-1234` |

**Official sources**

- [CPR Office — civil registration number](https://cpr.dk/english/civil-registration-number)
- [CPR-loven](https://www.retsinformation.dk/eli/lta/2023/1297)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
