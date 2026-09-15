# Sweden (`SE`)

National-ID patterns loaded when you pass `countries=["SE"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `PERSONAL_ID_SE` — Personnummer

The Swedish personal identity number. Ten or twelve digits with a hyphen before the last four.

| | |
|---|---|
| **Package type** | `PERSONAL_ID_SE` |
| **Shape this package looks for** | 6 or 8 digits + hyphen + 4 digits |
| **Checksum** | none in this package (Luhn is official) |
| **Example (synthetic)** | `811228-9874` |

**Official sources**

- [Skatteverket — personal identity number](https://skatteverket.se/servicelankar/otherlanguages/inenglish/individualsandemployees/livinginsweden/personalidentitynumberandcoordinationnumber.4.2cf1b5cd163796a5c8b4295.html)
- [Folkbokföringslag (1991:481)](https://www.riksdagen.se/sv/dokument-och-lagar/dokument/svensk-forfattningssamling/folkbokforingslag-1991481_sfs-1991-481/)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
