# India (`IN`)

National-ID patterns loaded when you pass `countries=["IN"]` (or `"all"`). Universal patterns always stay.



!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.


## `AADHAAR_IN` — Aadhaar

A 12-digit unique identity number issued by the Unique Identification Authority of India under the Aadhaar Act, 2016. UIDAI states that it is a random number and is not proof of citizenship.

| | |
|---|---|
| **Package type** | `AADHAAR_IN` |
| **Shape this package looks for** | 12 digits, optional spaces as 4 4 4. First digit is not 0 or 1. |
| **Checksum** | Verhoeff |
| **Example (synthetic)** | `2341 2341 2346` |

**Official sources**

- [UIDAI — Aadhaar](https://uidai.gov.in/en/my-aadhaar)
- [The Aadhaar (Targeted Delivery of Financial and Other Subsidies, Benefits and Services) Act, 2016](https://www.indiacode.nic.in/handle/123456789/2154)
- [UIDAI legal framework](https://uidai.gov.in/en/about-uidai/legal-framework.html)

## `PAN_IN` — Permanent Account Number (PAN)

A 10-character tax identifier issued by the Income Tax Department. It is used on returns and for specified financial transactions.

| | |
|---|---|
| **Package type** | `PAN_IN` |
| **Shape this package looks for** | 5 letters + 4 digits + 1 letter |
| **Checksum** | none |
| **Example (synthetic)** | `ABCDE1234F` |

**Official sources**

- [Income Tax Department — PAN](https://www.incometax.gov.in/iec/foportal/help/individual/return-preparation-help/permanent-account-number-pan)
- [Income-tax Act, 1961 s. 139A](https://incometaxindia.gov.in/pages/acts/income-tax-act.aspx)

## `GSTIN_IN` — GSTIN

The Goods and Services Tax Identification Number. It embeds a state code and a PAN.

| | |
|---|---|
| **Package type** | `GSTIN_IN` |
| **Shape this package looks for** | 2-digit state + PAN + entity + Z + check |
| **Checksum** | none in this package |
| **Example (synthetic)** | `27ABCDE1234F1Z5` |

**Official sources**

- [GST portal](https://www.gst.gov.in/)
- [Central Goods and Services Tax Act, 2017](https://www.indiacode.nic.in/handle/123456789/2276)

## `DRIVERS_LICENSE_IN` — Driving licence

Issued by state transport authorities. The common printed form starts with a two-letter state code.

| | |
|---|---|
| **Package type** | `DRIVERS_LICENSE_IN` |
| **Shape this package looks for** | State code + 2 digits + 11 digits, or state + hyphen + 13 digits |
| **Checksum** | none |
| **Example (synthetic)** | `MH12 20110012345` |

**Official sources**

- [Ministry of Road Transport — Parivahan](https://parivahan.gov.in/parivahan/)
- [Motor Vehicles Act, 1988](https://www.indiacode.nic.in/handle/123456789/1798)

The example values are synthetic or well-known public test numbers. Do not treat them as issued identifiers.
