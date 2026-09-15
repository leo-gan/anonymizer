# Ireland (`IE`)

National-ID patterns loaded when you pass `countries=["IE"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `PPS_IE` — PPS Number

The Personal Public Service Number. Used for social welfare, tax, and public services in Ireland. Common form is 7 digits plus a letter.

| | |
|---|---|
| **Package type** | `PPS_IE` |
| **Shape this package looks for** | 7 digits + A–W |
| **Checksum** | none |
| **Example (synthetic)** | `1234567T` |

**Official sources**

- [Gov.ie — PPS Number](https://www.gov.ie/en/service/12e6de-get-a-personal-public-service-pps-number/)
- [Social Welfare Consolidation Act 2005](https://www.irishstatutebook.ie/eli/2005/act/26/enacted/en/html)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
