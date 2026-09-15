# Poland (`PL`)

National-ID patterns loaded when you pass `countries=["PL"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `PESEL_PL` — PESEL

The Polish national identification number. Eleven digits encode birth date, serial, sex, and a check digit.

| | |
|---|---|
| **Package type** | `PESEL_PL` |
| **Shape this package looks for** | 11 digits |
| **Checksum** | weighted digits, last is the check |
| **Example (synthetic)** | `44051401359` |

**Official sources**

- [gov.pl — PESEL](https://www.gov.pl/web/gov/czym-jest-numer-pesel)
- [Ustawa o ewidencji ludności](https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20100002171)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
