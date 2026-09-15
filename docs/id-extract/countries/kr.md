# South Korea (`KR`)

National-ID patterns loaded when you pass `countries=["KR"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `RESIDENT_REGISTRATION_KR` — Resident registration number (주민등록번호)

The 13-digit number on the Korean resident registration card, usually written with a hyphen after the birth date.

| | |
|---|---|
| **Package type** | `RESIDENT_REGISTRATION_KR` |
| **Shape this package looks for** | 6 digits + hyphen + 7 digits |
| **Checksum** | none in this package |
| **Example (synthetic)** | `900101-1234567` |

**Official sources**

- [Ministry of the Interior and Safety — resident registration](https://www.mois.go.kr/eng/sub/a03/residentRegistration/screen.do)
- [Resident Registration Act](https://elaw.klri.re.kr/eng_service/lawView.do?hseq=59940&lang=ENG)

## `BUSINESS_REG_KR` — Business registration number (사업자등록번호)

A 10-digit number assigned by the National Tax Service to a business.

| | |
|---|---|
| **Package type** | `BUSINESS_REG_KR` |
| **Shape this package looks for** | NNN-NN-NNNNN |
| **Checksum** | none |
| **Example (synthetic)** | `123-45-67890` |

**Official sources**

- [National Tax Service — business registration](https://www.nts.go.kr/english/)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
