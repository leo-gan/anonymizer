# Japan (`JP`)

National-ID patterns loaded when you pass `countries=["JP"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `MY_NUMBER_JP` — Individual Number (My Number)

A 12-digit number assigned to each resident under the Social Security and Tax Number System.

| | |
|---|---|
| **Package type** | `MY_NUMBER_JP` |
| **Shape this package looks for** | 12 digits, optional spaces as 4 4 4 |
| **Checksum** | none in this package |
| **Example (synthetic)** | `1234 5678 9012` |

**Official sources**

- [Digital Agency — Individual Number](https://www.digital.go.jp/policies/mynumber)
- [Act on the Use of Numbers to Identify a Specific Individual in Administrative Procedures](https://www.japaneselawtranslation.go.jp/en/laws/view/2284)

## `RESIDENT_CARD_JP` — Residence card number (structural)

A coarse pattern for a residence-card serial (two letters + 8 digits).

| | |
|---|---|
| **Package type** | `RESIDENT_CARD_JP` |
| **Shape this package looks for** | 2 letters + 8 digits |
| **Checksum** | none |
| **Example (synthetic)** | `AB12345678` |

**Official sources**

- [Immigration Services Agency — residence card](https://www.moj.go.jp/isa/applications/procedures/nyuukokukanri10_00007.html)

## `DRIVERS_LICENSE_JP` — Driver licence number

A 12-digit Japanese driving-licence number.

| | |
|---|---|
| **Package type** | `DRIVERS_LICENSE_JP` |
| **Shape this package looks for** | 12 digits |
| **Checksum** | none |
| **Example (synthetic)** | `123456789012` |

**Official sources**

- [National Police Agency — driver’s licence](https://www.npa.go.jp/english/index.html)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
