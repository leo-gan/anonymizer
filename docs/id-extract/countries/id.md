# Indonesia (`ID`)

National-ID patterns loaded when you pass `countries=["ID"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `NIK_ID` — NIK (Nomor Induk Kependudukan)

The 16-digit population-administration number on the Indonesian KTP.

| | |
|---|---|
| **Package type** | `NIK_ID` |
| **Shape this package looks for** | 16 digits |
| **Checksum** | none |
| **Example (synthetic)** | `3174010101900001` |

**Official sources**

- [Dukcapil / Kemendagri — NIK](https://www.dukcapil.kemendagri.go.id/)
- [Undang-Undang Nomor 24 Tahun 2013 tentang Administrasi Kependudukan](https://peraturan.bpk.go.id/Details/38852)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
