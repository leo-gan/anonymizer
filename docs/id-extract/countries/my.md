# Malaysia (`MY`)

National-ID patterns loaded when you pass `countries=["MY"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `NRIC_MY` — MyKad / NRIC number

The 12-digit Malaysian identity-card number, written YYMMDD-PB-###G.

| | |
|---|---|
| **Package type** | `NRIC_MY` |
| **Shape this package looks for** | 6 digits + hyphen + 2 digits + hyphen + 4 digits |
| **Checksum** | none |
| **Example (synthetic)** | `900101-14-5678` |

**Official sources**

- [JPN — MyKad](https://www.jpn.gov.my/en/core-business/identity-card)
- [National Registration Act 1959](https://lom.agc.gov.my/)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
