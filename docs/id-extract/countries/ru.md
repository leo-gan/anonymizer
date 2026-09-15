# Russia (`RU`)

National-ID patterns loaded when you pass `countries=["RU"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `PASSPORT_RU` — Internal passport series and number

The series (4 digits) and number (6 digits) of the internal passport of a citizen of the Russian Federation.

| | |
|---|---|
| **Package type** | `PASSPORT_RU` |
| **Shape this package looks for** | 2 digits + optional space + 2 digits + optional space + 6 digits |
| **Checksum** | none |
| **Example (synthetic)** | `45 16 123456` |

**Official sources**

- [МВД — паспорт гражданина РФ](https://мвд.рф/mvd/structure1/Glavnie_upravlenija/guvm)
- [Federal Law No. 114-FZ (exit/entry) and Government passport statute](http://pravo.gov.ru/)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
