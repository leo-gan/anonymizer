# Presidio and id-extract

**Status:** maintainer research, 2026-09-22. The summary gaps are implemented on `id-extract-presidio-gaps`: SSN group exclusions, SIN leading digit, NPI leading digit, Personalausweis shape and check, DEA check digit, `ACN_AU`, `MEDICARE_AU`, `NHS_GB`, `UEN_SG`, `PASSPORT_GB`, and `HANDELSREGISTER_DE`. The opt-in catalog keys match `opt_in.py`. NRIC prefixes `F` and `M`, the Finnish check, the Thai and Turkish checks, and the German tax-id check are included. Plates, US healthcare labels, bank-account digit runs, postal codes, and a default UUID stay unported.  
**Audience:** maintainers only  
**Do not publish.** `docs/internal/` is excluded from the MkDocs build.

This note compares structured identifiers. It is the backlog for making `id-extract` cover more official numbers, and for making each number's description, expression, and source link more precise. It is not a plan to copy Presidio's context-word scorer.

Sources read for this note:

- Presidio `main` on 2026-09-22: [`predefined_recognizers`](https://github.com/microsoft/presidio/tree/main/presidio-analyzer/presidio_analyzer/predefined_recognizers) and [supported entities](https://microsoft.github.io/presidio/supported_entities/).
- `id-extract` 0.2.0 in this repo: 109 patterns on by default, 16 more with `opt_in="all"`, and 15 further keys that load only when named. Country pages are generated from `scripts/gen_id_extract_country_docs.py`.

A hit in either library means the text matched a shape. It does not mean an agency issued the value.

## What each library decides

Presidio Analyzer finds personally identifiable information and returns a type plus a score from 0 to 1. A pattern recognizer has three levers: a regular expression, context words near the match that raise the score, and an optional check that drops the match (checksum, denied sample, illegal prefix). The same repository also runs spaCy, Stanza, transformers, or GLiNER for names and places, and it can call Azure Language. Those are not identifier grammars.

`id-extract` returns a span and a type. It uses [google-re2](https://github.com/google/re2). RE2 has no lookahead, lookbehind, or backreference, so a Presidio expression that starts with `(?<=...)` or `(?!...)` cannot be copied. There is no context window. A checksum failure usually keeps the span and relabels it `TYPE_LIKE`. Four broad types drop the span instead: `RTN_US`, `CUSIP_NNA`, `PHN_BC_CA`, and `CLABE_MX`. State, provincial, and industry patterns stay off unless `opt_in` is set.

| Question | Presidio | id-extract |
|---|---|---|
| What is a confident hit? | Score after context words, often from a weak pattern at 0.05–0.3 | The expression matched, and a strict checksum did not fail |
| How are ambiguous digit runs handled? | Left at a low score unless a nearby word such as "ssn" or "nhs" appears | Left off the default map, or kept only when a checksum passes |
| Where is the official definition? | Sometimes a URL in the recognizer file; the public entity table is often one sentence and often Wikipedia | Country and universal pages: definition, shape, synthetic example, checksum, issuing-agency link |
| Where is the expression? | Next to the recognizer class | Only in the country plugin or `opt_in.py`, not beside the source link |

Presidio is more precise when a checksum or an illegal prefix exists and `id-extract` does not apply it. `id-extract` is more precise when the grammar itself is tight enough to run with every country enabled, because it cannot ask whether the word "passport" is nearby.

## Coverage

Presidio's pattern pack, excluding name/place models and Azure adapters, is about 90 entity types in 18 countries plus global types (card, IBAN, email, phone, IP, URL, crypto, UUID, date). The deep country packs are the United States, the United Kingdom, Germany, India, Italy, Korea, South Africa, and Australia.

`id-extract` ships 36 country plugins. It already covers Japan, Hong Kong, Taiwan, New Zealand, Brazil, Argentina, France, Mexico, and several European personal numbers that Presidio does not ship. Presidio's extra countries are Nigeria and the Philippines. Presidio's extra depth is German registration numbers, Australian company and Medicare numbers, the UK NHS number, the Singapore UEN, and a set of US healthcare labels.

## Same identifier, different precision

| Identifier | id-extract | Presidio | What to change in id-extract |
|---|---|---|---|
| US SSN | `SSN_US` is only `AAA-GG-SSSS`. Values that start with 9 are ITIN or ATIN instead. | Five patterns, including a bare 9-digit run at score 0.05. Drops area `000` and `666`, group `00`, serial `0000`, all-identical digits, and the sample numbers `078051120`, `123456789`, and `987654320`. | Keep the hyphenated shape. Reject those SSA-invalid groups in the expression. Do not add a bare 9-digit SSN. Source already on the US page: [POMS RM 10201.030](https://secure.ssa.gov/poms.nsf/lnx/0110201030). |
| US ITIN | Hyphenated, IRS ranges 50–65, 70–88, 90–92, 94–99. | Same ranges, and also a space or a single hyphen in either gap. | The hyphenated form is the precise one. A second pattern with the same ranges and one separator is optional. Do not take the unhyphenated weak pattern. |
| US NPI | Any 10 digits that pass the CMS Luhn check over `80840` + the number. | Same check, and the first digit must be 1 or 2. | Restrict the expression to `[12]\d{9}`. Source: [CMS NPI standard](https://www.cms.gov/regulations-and-guidance/administrative-simplification/nationalprovidentstand). |
| US EIN | `\d{2}-\d{7}`, always on. | The healthcare "provider tax ID" recognizer is mostly a labelled lookbehind. Its weak pattern uses a list of IRS campus prefixes. | Keep `EIN_US` as its own type. Restrict the first two digits to prefixes on [Valid EINs](https://www.irs.gov/businesses/small-businesses-self-employed/valid-eins). |
| DEA number | `DEA_US` is two letters, seven digits, optional suffix. No check digit. `MEDICAL_LICENSE_US` is a still wider letter-plus-digits run. | `MEDICAL_LICENSE` is the DEA body, with a registrant-letter class and the DEA check digit. The cited page is a vendor blog, not the DEA. | Add the check digit to `DEA_US` and cite the [DEA Practitioner's Manual](https://www.deadiversion.usdoj.gov/GDP/%28DEA-DC-071%29%28EO-DEA226%29_Practitioner%27s_Manual_%28final%29.pdf) and [21 CFR 1301.22](https://www.ecfr.gov/current/title-21/chapter-II/part-1301/section-1301.22). Do not cite the vendor blog. |
| ABA routing / RTN | `RTN_US` is opt-in, Federal Reserve prefix bands, strict checksum drop. | `ABA_ROUTING_NUMBER`: first digit in `0,1,2,3,6,7,8`, optional hyphenation, checksum. No URL in the file. | Keep the stricter prefix bands. Presidio is the coarser pattern. |
| Canadian SIN | Hyphenated 9 digits plus Luhn. | Luhn, and the first digit is 1–7 or 9 (0 and 8 are not issued). | Exclude a leading 0 or 8. Source: [ESDC SIN](https://www.canada.ca/en/employment-social-development/services/sin.html). |
| UK passport | `GB_PASSPORT` is 9 digits. | `[A-Z]{2}\d{7}` for books issued from 2015, score 0.1, context required in practice. No URL in the file. | Add the 2015 shape as its own type, beside the 9-digit pattern. Cite HM Passport Office, not only the recognizer docstring. |
| Singapore NRIC / FIN | `NRIC_SG` is `S`, `G`, or `T`, seven digits, a letter. | `S`, `T`, `F`, `G`, or `M`. The file cites Wikipedia. | Extend the prefix class to `STFGM` after checking [ICA Singpass / ICA NRIC](https://www.ica.gov.sg/) rather than Wikipedia. |
| Finnish henkilötunnus | `HETU_FI` allows century marks `+`, `-`, and `A`, and any final alphanumeric. | Century marks `-+ABCDEFYXWVU` and a restricted check character, plus the check. Source: [DVV](https://dvv.fi/en/personal-identity-code). | Use the DVV character classes and the check. A failed check should become `HETU_FI_LIKE`. |
| Thai national ID | `NATIONAL_ID_TH` is any 13 digits. | 13 digits plus the official check. | Add the check. Without it this pattern collides with every 13-digit token. |
| Turkish TCKN | `NATIONAL_ID_TR` is any 11 digits. | 11 digits plus the NVI check. Source: [tckimlik.nvi.gov.tr](https://tckimlik.nvi.gov.tr/). | Add the check. Eleven digits already collide with `NSS_MX`, `AMKA_GR`, `STEUER_ID_DE`, and `PESEL_PL` when several countries are on. |
| German tax ID | `STEUER_ID_DE` is any 11 digits. | First digit 1–9, ISO 7064 mod 11,10. The entity page cites §§ 139a–139e AO. The recognizer file has no URL. | Add that check and link the statute. Same 11-digit collision as the Turkish number. |
| German ID card | `PERSONALAUSWEIS_DE` is 9 or 10 alphanumeric characters. | nPA: ICAO character set (no A, B, D, E, I, O, Q, S, U) plus an ICAO check digit; legacy `T` plus 8 digits. | Replace the broad pattern with those two shapes and the check. Legal basis named by Presidio: Personalausweisgesetz. |
| German driving licence | `DRIVERS_LICENSE_DE` is 11 or 12 alphanumeric characters. | `[A-Z]{2}\d{8}[A-Z0-9]`, no checksum in the file. | Prefer that shape. It is still not proof of issue. |
| IBAN | Country-length table and ISO 13616 mod-97. A failure becomes `IBAN_LIKE`. | One generic expression with lookbehind, then a checksum. | Keep the length table. The lookbehind is not portable. |
| UUID / Mexican folio | `FOLIO_FISCAL_MX` is any hyphenated hex UUID, opt-in, because a UUID is not by itself a SAT folio. | Generic `UUID` with RFC 4122 / RFC 9562 version and variant nibbles. Nil UUID dropped. Sources: [RFC 4122](https://datatracker.ietf.org/doc/html/rfc4122), [RFC 9562](https://datatracker.ietf.org/doc/html/rfc9562). | Do not add a default `UUID` type. If the folio stays, require a version nibble `1`–`8` and a variant nibble `8`, `9`, `A`, or `B`, and keep it opt-in. |
| US driver licence | Broad on purpose. Florida has its own opt-in grammar. The page cites AAMVA. | A very wide alphanumeric pattern. The only link is `https://ntsi.com/drivers-license-format/`, which is not a government standard. | Do not copy it. Keep adding one state only when that state publishes a character grammar. |

## Identifiers to add

Add a type only when the expression is RE2-safe, the format is published, and the country page can link the issuer. Where Presidio's own link is Wikipedia, a gist, or a vendor blog, use the issuer instead. A 9-, 10-, or 11-digit pattern joins the default map only with a checksum that drops or relabels on failure. Otherwise it stays opt-in, the same rule as `I94_US` and the bare provincial health numbers.

| Proposed key | Presidio type | Shape to implement | Check | Load | Source to cite |
|---|---|---|---|---|---|
| `ACN_AU` | `AU_ACN` | 9 digits, printed `NNN NNN NNN` | ASIC modified mod-10. Do not ship the bare 9-digit pattern without the check. | Default, strict or `_LIKE` | ASIC. Presidio links only [asic.gov.au](https://asic.gov.au/). Open the company-number page and cite that URL, not the homepage alone. |
| `MEDICARE_AU` | `AU_MEDICARE` | First digit 2–6, then 9 digits; printed in groups | Medicare check digit | Default only with the check. Ten digits collide with NPI. | Services Australia. Presidio cites [Wikipedia](https://en.wikipedia.org/wiki/Medicare_card_(Australia)). Do not use that as the package source. |
| `NHS_GB` | `UK_NHS` | 10 digits, optional spaces or hyphens in the 3-3-4 print form | Modulus 11. Weights 10 through 2 on the first nine digits. Check digit = 11 − (sum mod 11). A result of 11 is stored as 0. A result of 10 is not issued. | Strict drop. A 10-digit run is also an NPI. | [NHS number](https://digital.nhs.uk/services/nhs-number) and [ISB 0149](https://digital.nhs.uk/data-and-information/information-standards/information-standards-and-data-collections-including-extractions/publications-and-notifications/standards-and-collections/isb-0149-nhs-number). The recognizer file has no URL. |
| `UEN_SG` | `SG_UEN` | `\d{8}[A-Z]`, `\d{9}[A-Z]`, or `[TSR]\d{2}[A-Z]{2}\d{4}[A-Z]` | The three UEN checks (business, local company, and other entities) | Default with the check | [UEN](https://www.uen.gov.sg/). Presidio cites a personal gist. Do not cite the gist. |
| `ORGANISATIONSNUMMER_SE` | `SE_ORGANISATIONSNUMMER` | 10 digits; the third digit distinguishes an organisation from a personnummer | Luhn, as for the personal number | Default with the check | Skatteverket or Bolagsverket. The recognizer file has no URL; find the agency page before shipping. |
| `PASSPORT_GB_2015` | `UK_PASSPORT` | `[A-Z]{2}\d{7}` | none published here | Default. Two letters plus seven digits is distinctive enough. | HM Passport Office. Keep the existing 9-digit `GB_PASSPORT` until a source says those numbers are unused. |
| `HANDELSREGISTER_DE` | `DE_HANDELSREGISTER` | `HR[AB]` plus optional space plus 1–6 digits | none | Default. The prefix is the grammar. | HGB §§ 9 and 14, as named on Presidio's entity page. Link the statute text. |
| `RVNR_DE` | `DE_SOCIAL_SECURITY` | 2-digit area, birth day, month, year, initial, serial, check | Deutsche Rentenversicherung check | Default with the check | SGB VI § 147, as named by Presidio. The file has no URL. |
| `KVNR_DE` | `DE_HEALTH_INSURANCE` | One letter plus 9 digits | GKV check | Default with the check. A letter plus nine digits is otherwise a common token. | SGB V § 290. |
| `PASSPORT_ZA` | `ZA_PASSPORT` | Prefix `A`, `D`, `M`, or `T`, then 8 digits | prefix list | Default | Department of Home Affairs. Presidio's file cites Wikipedia. |
| `VAT_ZA` | `ZA_VAT_NUMBER` | 10 digits starting with 4 | prefix, and any SARS check the agency publishes | Default only if the check exists; otherwise opt-in. `TAX_ZA` is already any 10 digits. | SARS. Do not cite the CDQ data-model URL Presidio uses. |
| `NIN_NG` | `NG_NIN` | 11 digits | NIMC check, if the agency page states it | New country plugin `NG`. Strict or `_LIKE`. | Presidio cites [nimc.gov.ng](https://nimc.gov.ng/). That host did not answer on 2026-09-22. Confirm the check on a page that loads before coding. Eleven digits collide with other national numbers. |
| `TIN_PH` | `PH_TIN` | 9 or 12 digits | BIR check | New country plugin `PH`, only with the check | [BIR](https://www.bir.gov.ph/). |
| `EPIC_IN` | `IN_VOTER` | 3 letters plus 7 digits, with the second-letter class the Election Commission publishes | none in Presidio | Default if the letter class is cited; otherwise skip | Election Commission of India. Presidio cites [Wikipedia](https://en.wikipedia.org/wiki/Voter_ID_(India)). |

Indian vehicle plates, German plates, UK plates, and South African plates are real published formats, and several of Presidio's expressions use lookahead or lookbehind. Port one plate family only after the expression is rewritten without those operators and the transport agency page is linked. Do not start with Presidio's nine Indian vehicle patterns.

## Do not port

These Presidio entities are broad, labelled, or not an identifier grammar. Copying them would make `countries="all"` noisier, which is the opposite of a more precise catalog.

| Presidio type | Why it stays out |
|---|---|
| `US_BANK_NUMBER` | 8 to 17 digits, score 0.05, no checksum, no URL. |
| `US_CLAIM_NUMBER`, `US_PRIOR_AUTHORIZATION_NUMBER`, `US_PRESCRIPTION_NUMBER`, `US_REFERRAL_NUMBER` | CMS describes these as payer-assigned values and does not publish one syntax. The useful Presidio patterns are lookbehinds anchored on words such as "claim" or "prior auth". `id-extract` cannot see those words. The weak `CLM-` / `PA-` / `RX-` prefixes are not a standard. |
| `US_HEALTH_INSURANCE_MEMBER_ID` | The expression uses lookahead, and the recognizer's own comment says there is no universal card syntax. |
| `US_PROVIDER_TAX_ID` | This is an EIN with a label. Tighten `EIN_US` instead of adding a second type. |
| `DE_BSNR`, `DE_LANR` | Bare 9-digit runs. Presidio leans on context words. |
| `DE_PLZ`, `UK_POSTCODE`, `CA_POSTAL_CODE` | Postal codes. Presidio marks the German postcode as high false-positive risk at score 0.05. |
| `DE_KFZ` and other plate patterns that require lookaround | Rewrite from the regulation, or skip. |
| `IN_VEHICLE_REGISTRATION` patterns that use `(?!0000)` | Same RE2 limit. |
| `IN_PASSPORT` | One weak pattern. The file cites a travel-insurance blog. |
| `PH_UMID` | Presidio ships it disabled. Twelve digits with no check collides with other identifiers. |
| `PERSON`, `LOCATION`, `NRP`, `DATE_TIME` prose dates, medical NER labels | Not identifier shapes. Dates in `id-extract` stay `DATE_ISO`. |
| Generic `UUID` as a default type | Collides with the decision that a UUID is not automatically a Mexican folio. |

## What id-extract already has that Presidio does not

Presidio's US pack stops at SSN, ITIN, passport, driver licence, bank account, routing number, NPI, MBI, DEA-style medical licence, and labelled healthcare tokens. `id-extract` also ships ATIN, PTIN, A-Number, USCIS receipt, DOS case ID, and EIN as a first-class type, plus opt-in Florida licence, RTN, CUSIP, FFL, N-number, HIN, and California payroll account.

Presidio's Canada pack is SIN and postal code. `id-extract` also ships the CRA program account, DIN, NPN, DIN-HM, UCI, and the opt-in provincial health and licence patterns.

Presidio has no Mexico plugin. `id-extract` ships CURP, RFC, CLABE (strict), NSS, pedimento, and an opt-in folio fiscal.

Also absent from Presidio's pattern pack, and present here: Japan My Number and residence card, Hong Kong identity card, Taiwan national ID, New Zealand IRD, Brazil CPF / CNPJ / RG, Argentina DNI, France INSEE and passport, Spain CIF, Belgium NISS, Switzerland AHV and VAT, Austria SVNR, Netherlands BSN, Ireland PPS, Israel identity number, Russia passport, Indonesia NIK, Malaysia NRIC, China resident ID and unified social credit code.

## Source links that are still weak

The generated country pages are already the right shape: one definition, the package key, the shape, whether a checksum runs, a synthetic example, and agency links. Three gaps remain.

The expression is not on the page. A reader can see "10 digits" and cannot see `\b[12]\d{9}\b` without opening the plugin. For each type this note changes, put the RE2 expression in the generator entry next to the source URL, and render it on the country page. The page should still say that the expression is a structural approximation.

The opt-in catalog still uses research names that are not the package keys. The California payroll row is `PAYROLL_US_CA` in `docs/id-extract/opt-in-us-ca-mx.md`, while the pattern key is `EDD_PAYROLL_US`. The same page is the source list for explicit keys such as `UEI_US` and `I94_US`. Rename the catalog rows to the keys in `opt_in.py` so the link, the description, and the expression refer to one identifier.

Presidio's public table is not a source list to import. Wikipedia, a GitHub gist, `ntsi.com`, and a vendor DEA blog are not issuing authorities. When a Presidio recognizer names a statute in a docstring and does not link it, the `id-extract` page should link the statute.

## Suggested order

1. Tighten keys that already exist and already have a source: SSN invalid groups, SIN leading digit, NPI leading digit, NRIC prefixes, HETU, Thai and Turkish checks, German tax-id check, German ID-card shapes, DEA check digit.
2. Add the distinctive new keys whose grammar does not need a context word: `HANDELSREGISTER_DE`, the 2015 UK passport, `PASSPORT_ZA`, `UEN_SG`, `ACN_AU`, `NHS_GB`, `MEDICARE_AU`.
3. Add organisation and new-country numbers only after the checksum is copied from the agency page: Swedish organisation number, Nigerian NIN, Philippine TIN.
4. Leave plates, US healthcare labels, bank-account digit runs, and postal codes unported.

Each added key needs a row in the country generator (definition, expression, synthetic example, checksum, source URL) and a test that a known-valid synthetic passes and a one-digit change fails when a check exists.
