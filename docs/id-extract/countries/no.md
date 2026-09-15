# Norway (`NO`)

National-ID patterns loaded when you pass `countries=["NO"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `NATIONAL_ID_NO` — Fødselsnummer

The Norwegian national identity number. Eleven digits: date of birth plus an individual number and two check digits.

| | |
|---|---|
| **Package type** | `NATIONAL_ID_NO` |
| **Shape this package looks for** | 11 digits |
| **Checksum** | none in this package |
| **Example (synthetic)** | `01018012345` |

**Official sources**

- [Skatteetaten — national identity number](https://www.skatteetaten.no/en/person/national-registry/identitetsnummer/fodselsnummer/)
- [Folkeregisterloven](https://lovdata.no/dokument/NL/lov/2016-12-09-88)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
