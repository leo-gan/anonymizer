# Austria (`AT`)

National-ID patterns loaded when you pass `countries=["AT"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `SVNR_AT` — Sozialversicherungsnummer

The Austrian social-insurance number. Ten digits; the last six encode the date of birth.

| | |
|---|---|
| **Package type** | `SVNR_AT` |
| **Shape this package looks for** | 10 digits |
| **Checksum** | none in this package |
| **Example (synthetic)** | `1237010180` |

**Official sources**

- [ÖGK — Sozialversicherungsnummer](https://www.gesundheitskasse.at/cdscontent/?contentid=10007.821578)
- [ASVG](https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=10008147)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
