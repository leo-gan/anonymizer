# Universal identifiers

These patterns load for every call. They are not tied to one ISO-2 country plugin. Some national passports sit here because their keys have no country suffix the filter understands (`US_PASSPORT`, `CA_PASSPORT`, `GB_PASSPORT`).

!!! warning "Structural match only"
    A hit means the text looked like the identifier. It is not a finding that a payment network, a bank, or a passport office issued the value.

## Communication and network

| Type | What it is | Shape this package looks for | Example (synthetic) | Sources |
|---|---|---|---|---|
| `EMAIL` | Mailbox address | Local part, `@`, domain | `ada@example.com` | [RFC 5321](https://www.rfc-editor.org/rfc/rfc5321), [RFC 5322](https://www.rfc-editor.org/rfc/rfc5322) |
| `PHONE` | Telephone number | Optional `+`, groups of digits | `+1 202 555 0100` | [ITU-T E.164](https://www.itu.int/rec/T-REC-E.164/) |
| `URL` | HTTP(S) locator | `http://` or `https://` plus host | `https://example.com/a` | [RFC 3986](https://www.rfc-editor.org/rfc/rfc3986) |
| `IPV4_ADDRESS`, `IP_ADDRESS` | IPv4 address | Four octets 0–255 | `192.0.2.10` | [RFC 791](https://www.rfc-editor.org/rfc/rfc791) |
| `IPV6_ADDRESS` | IPv6 address | Colon-separated hex groups | `2001:db8::1` | [RFC 4291](https://www.rfc-editor.org/rfc/rfc4291) |
| `MAC_ADDRESS` | Hardware address | Six hex octets | `00:1A:2B:3C:4D:5E` | [IEEE 802](https://standards.ieee.org/ieee/802/1048/) |

`IP_ADDRESS` is a legacy alias of the IPv4 pattern.

## Payments and assets

| Type | What it is | Shape | Checksum | Example (synthetic) | Sources |
|---|---|---|---|---|---|
| `CREDIT_CARD` | Payment-card primary account number | 13–19 digits, optional spaces or dashes | Luhn ([ISO/IEC 7812](https://www.iso.org/standard/70484.html)) | `4111111111111111` | [ISO/IEC 7812](https://www.iso.org/standard/70484.html), [PCI DSS](https://www.pcisecuritystandards.org/) |
| `IBAN` | International Bank Account Number | ISO-2 + 2 check digits + BBAN | ISO 13616 mod-97 | `DE89370400440532013000` | [ISO 13616-1:2020](https://www.iso.org/standard/81090.html), [SWIFT IBAN Registry](https://www.swift.com/resource/iban-registry-pdf) |
| `BIC_SWIFT` | Business Identifier Code | 8 or 11 letters/digits | none | `DEUTDEFF` | [ISO 9362](https://www.iso.org/standard/84108.html) |
| `CURRENCY_AMOUNT` | Amount with a currency code or symbol | Code/symbol plus grouped digits | none | `EUR 1,250.00` | Descriptive only |
| `CRYPTO_BTC` | Bitcoin address | Base58 or Bech32 `bc1…` | none | `bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4` | [BIP 173](https://github.com/bitcoin/bips/blob/master/bip-0173.mediawiki) |
| `CRYPTO_ETH` | Ethereum account | `0x` + 40 hex digits | none | `0x0000000000000000000000000000000000000000` | [Ethereum yellow paper](https://ethereum.github.io/yellowpaper/paper.pdf) |
| `VIN` | Vehicle identification number | 17 characters, no I/O/Q | ISO 3779 | `1HGCM82633A004352` | [ISO 3779](https://www.iso.org/standard/52200.html) |

A failed card, IBAN, or VIN check becomes `CREDIT_CARD_LIKE`, `IBAN_LIKE`, or `VIN_LIKE`.

## Dates and passports stored as universal

| Type | What it is | Shape | Example (synthetic) | Sources |
|---|---|---|---|---|
| `DATE_ISO` | Calendar date, optional time | `YYYY-MM-DD` and optional ISO time | `2026-09-15T12:00:00Z` | [ISO 8601](https://www.iso.org/iso-8601-date-and-time-format.html) |
| `US_PASSPORT` | United States passport number | Letter + 8 digits, or 9 digits | `A12345678` | [U.S. Department of State — Passports](https://travel.state.gov/content/travel/en/passports.html), [ICAO Doc 9303](https://www.icao.int/publications/pages/publication.aspx?docnum=9303) |
| `CA_PASSPORT` | Canadian passport number | Two letters + 6 digits | `AB123456` | [IRCC — Canadian passports](https://www.canada.ca/en/immigration-refugees-citizenship/services/canadian-passports.html), ICAO 9303 |
| `GB_PASSPORT` | United Kingdom passport number | 9 digits | `123456789` | [GOV.UK — Passports](https://www.gov.uk/browse/abroad/passports), ICAO 9303 |

Those three passport keys stay in the universal map so a `--countries GB` filter does not drop `US_PASSPORT`. That is a limitation of the current key names, not a claim that U.S. passports are issued in every country.
