# Opt-in identifiers: United States, Canada, and Mexico

Federal identifiers with a selective shape are in the [country catalog](countries/index.md) and load with `countries=`. State, provincial, and industry identifiers on this page load only when you pass `opt_in`.

```python
from id_extract import extract

extract(text, countries=["US"], opt_in="all")
extract(text, opt_in=["LICENSE_IL_US", "UEI_US"])
```

`"all"` loads the selective rows: a letter-and-digit shape, or a digit run that is kept only when its check digit passes. Naming a key loads that key, including a bare digit run. `available_opt_in()` lists every key.

A hit means the text had that shape. It does not mean the issuer assigned the value.

## Federal identifiers that stay opt-in

A few federal numbers are opt-in because a default pattern would match unrelated tokens.

| Key | Why it is not in the country plugin |
|---|---|
| `I94_US` | 11 digits, the same shape as `NSS_MX` |
| `UEI_US` | 12 alphanumeric characters |
| `FOLIO_FISCAL_MX` | A UUID, which appears outside Mexican invoices |
| `OCR_INE_MX`, `REGISTRO_PATRONAL_MX` | A 12- or 13-digit run, or 11 alphanumeric characters |

The INE voter key is 18 characters. The cited INE note does not fix the character order, and a loose 18-character pattern also matches `CURP_MX`. It is not implemented.

The research tables below are the source list. A row whose key is in `available_opt_in()` is implemented. A federal row that now lives on the country page is listed there.

## How to read Fit

| Fit | What the next version should do |
|---|---|
| **Strong** | Search for the shape on its own. The character classes are selective. |
| **Check** | Search for the shape, then keep the hit only when the check digit passes. |
| **Keyword** | The shape is official, and the same digits appear in other numbers. Search only when the official name is nearby. |

## Already in the country or universal set

Do not add a second pattern for these. A tighter opt-in pattern may still be worth shipping when the row below says it wins an overlap.

| Already emitted | Identifier |
|---|---|
| `SSN_US`, `SSN` | Social Security number |
| `EIN_US` | Employer Identification Number |
| `MEDICAL_NPI_US` | National Provider Identifier |
| `DRIVERS_LICENSE_US` | Broad state driver-licence token |
| `MEDICAL_LICENSE_US` | Broad medical or DEA-style token |
| `SIN_CA` | Social Insurance Number, hyphenated |
| `DRIVERS_LICENSE_CA` | Broad provincial licence token |
| `CURP_MX`, `RFC_MX` | CURP and RFC |
| `US_PASSPORT`, `CA_PASSPORT` | Passport numbers in the universal map |
| `VIN`, `CREDIT_CARD`, `IBAN` | Universal vehicle and payment identifiers |

## United States

`US_CA` in a key is the USPS abbreviation for California. It is not the Canada plugin `CA`.

| Proposed key | Identifier | Level | Shape | Fit | Example | Source |
|---|---|---|---|---|---|---|
| `ITIN_US` | Individual Taxpayer Identification Number | Federal | 9 digits, `9NN-NN-NNNN`. The 4th and 5th digits are 50–65, 70–88, 90–92, or 94–99. | Strong | `900-70-0000` | [IRS TIN](https://www.irs.gov/tin/taxpayer-identification-numbers-tin), [IRM 3.21.263](https://www.irs.gov/irm/part3/irm_03-021-263r) |
| `ATIN_US` | Adoption Taxpayer Identification Number | Federal | `9NN-93-NNNN` | Strong | `900-93-0000` | [IRM 3.13.40](https://www.irs.gov/irm/part3/irm_03-013-040) |
| `PTIN_US` | Preparer Tax Identification Number | Federal | `P` and 8 digits | Strong | `P00000000` | [IRM 3.12.2](https://www.irs.gov/irm/part3/irm_03-012-002r) |
| `MBI_US` | Medicare Beneficiary Identifier | Federal | 11 characters. Position rules are under the table. Dashes are printed on the card and are not part of the stored value. | Strong | `1EG4-TE5-MK73` | [CMS format sheet](https://www.cms.gov/medicare/new-medicare-card/understanding-the-mbi-with-format.pdf) |
| `A_NUMBER_US` | Alien Registration Number | Federal | `A` and 7, 8, or 9 digits. A shorter number is padded to 9 digits in current systems. | Strong | `A000000001` | [USCIS glossary](https://www.uscis.gov/glossary-term/50684) |
| `USCIS_RECEIPT_US` | USCIS receipt number | Federal | 3 letters and 10 digits | Strong | `ABC0000000001` | [USCIS receipt field](https://my.uscis.gov/accounts/annual-asylum-fee/questionnaire) |
| `DOS_CASE_US` | Department of State immigrant case ID | Federal | 3 letters and 9 or 10 digits. A Diversity Visa case is 4 digits, 2 letters, and 5 digits. | Strong | `XYZ0123456789` | [USCIS immigrant-fee page](https://www.uscis.gov/forms/filing-fees/uscis-immigrant-fee/immigrant-fee-payment-tips-on-finding-your-a-number-and-dos-case-id) |
| `I94_US` | Form I-94 admission number | Federal | 11 digits | Keyword | `00000000001` | [Form G-845 instructions](https://www.uscis.gov/sites/default/files/document/forms/g-845instr.pdf) |
| `DEA_US` | DEA registration number | Federal | 2 letters and 7 digits. The seventh digit is a check digit. Under [21 CFR 1301.22(c)](https://www.ecfr.gov/current/title-21/chapter-II/part-1301/section-1301.22) a hospital may add a hyphen and an internal suffix. | Strong | `AB1234563` | [DEA Practitioner's Manual](<https://www.deadiversion.usdoj.gov/GDP/(DEA-DC-071)(EO-DEA226)_Practitioner's_Manual_(final).pdf>) |
| `NDC_US` | National Drug Code | Federal | 10 or 11 digits in segments `4-4-2`, `5-3-2`, `5-4-1`, `6-3-2`, or `6-4-1`, with hyphens. A 12-digit `6-4-2` form takes effect on 7 March 2033. | Strong | `0000-0000-00` | [21 CFR 207.33](https://www.ecfr.gov/current/title-21/chapter-I/subchapter-C/part-207/subpart-C), [FDA format page](https://www.fda.gov/drugs/electronic-drug-registration-and-listing-system-edrls/national-drug-code-format) |
| `CLIA_US` | CLIA laboratory number | Federal | 10 characters: 2-digit state code, the letter `D`, and 7 digits | Strong | `12D0000001` | [CMS State Operations Manual, ch. 6, §6008](https://www.cms.gov/regulations-and-guidance/guidance/manuals/downloads/som107c06pdf.pdf) |
| `RTN_US` | ABA routing transit number | Industry | 9 digits. The first two digits are `00`–`12`, `21`–`32`, `61`–`72`, or `80`. The 9th digit is a check digit. | Check | `010000000` | [ABA routing-number policy](https://www.aba.com/news-research/analysis-guides/routing-number-policy-procedures), [12 CFR Part 229 Appendix A](https://www.law.cornell.edu/cfr/text/12/appendix-A_to_part_229) |
| `CUSIP_US_CA` | CUSIP | Industry | 9 characters: 6-character issuer, 2-character issue, numeric check digit. The check is the Modulus 10 double-add-double method. The same number is the NSIN for the United States and Canada. | Check | `AAA000AA0` | [CUSIP structure](https://www.cusip.com/identifiers.html), [CGS identifier guide](https://storage.pardot.com/1012812/1724352321TRtwcVEZ/Inside_the_CGS_Identification_System.pdf) |
| `FFL_US` | Federal firearms licence number | Federal | 15 characters in groups `1-2-3-2-2-5`. The 5th group may contain a letter. | Strong | `9-99-999-99-6B-99999` | [ATF FFL eZ Check mask](https://fflezcheck.atf.gov/FFLEzCheck/fflDownload) |
| `N_NUMBER_US` | FAA aircraft registration (N-number) | Federal | `N` plus 1 to 5 symbols: 1–5 digits, or 1–4 digits and one suffix letter, or 1–3 digits and two suffix letters. `I` and `O` are excluded. The first character after `N` is not `0`. | Strong | `N12345` | [14 CFR 47.15](https://www.ecfr.gov/current/title-14/chapter-I/subchapter-C/part-47/subpart-A/section-47.15), [FAA forming an N-number](https://www.faa.gov/licenses_certificates/aircraft_certification/aircraft_registry/forming_nnumber) |
| `HIN_US` | Hull identification number | Federal | 12 characters, no separators. Characters 4–8 exclude `I`, `O`, and `Q`. Character 9 is `A`–`L` (month). Character 10 and characters 11–12 are digits. | Strong | `ABC12A34A485` | [33 CFR 181.25](https://www.ecfr.gov/current/title-33/part-181/subpart-C) |
| `DL_FL_US` | Florida driver licence or ID number | State | 1 letter and 12 digits. The portal shows `LNNN-NNN-NN-NNN-N`. Since 31 July 2024 the assignment is randomized and still uses this shape. | Strong | `Z123-456-78-901-0` | [FLHSMV UTC manual](https://www.flhsmv.gov/pdf/courts/utc/utccombinedmanual.pdf), [FLHSMV 2024 notice](https://www.flhsmv.gov/2024/07/19/flhsmv-implements-legislation-requiring-driver-licenses-and-identification-card-numbers-to-change/), [status-check example](https://services.flhsmv.gov/dlcheck/) |
| `EDD_PAYROLL_US` | California EDD employer payroll-tax account | State | 8 digits, printed `NNN-NNNN-N` | Strong | `000-0000-0` | [EDD registration](https://edd.ca.gov/en/payroll_taxes/am_i_required_to_register_as_an_employer/) |
| `LICENSE_US_IL` | Illinois professional licence (IDFPR) | State | 9 digits. The first 3 are the profession code. | Keyword | `000000000` | [IDFPR bulk-lookup format](https://idfprapps.illinois.gov/LicenseLookUp/BulkLookupHelp.asp) |
| `UEI_US` | Unique Entity Identifier (SAM.gov) | Federal | 12 alphanumeric characters. SAM.gov states that length. A GSA FAQ points to a technical specification for any excluded characters, so the first expression should allow letters and digits. | Keyword | `ABC012345678` | [SAM.gov: 12-character Unique Entity ID](https://sam.gov/search), [GSA Entity Management API](https://open.gsa.gov/api/entity-api/) |
| `TAXONOMY_US` | NUCC Health Care Provider Taxonomy | Industry | 10 alphanumeric characters. NUCC says the code has no internal structure, so the last character is not a fixed letter. | Keyword | `A000000000` | [NUCC taxonomy](https://nucc.org/taxonomy) |

### MBI positions

Letters exclude `S`, `L`, `O`, `I`, `B`, and `Z`. CMS publishes the card sample `1EG4-TE5-MK73`.

| Position | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Class | digit `1`–`9` | letter | letter or digit | digit | letter | letter or digit | digit | letter | letter | digit | digit |

### Overlaps with the current US plugin

`ITIN_US` and `ATIN_US` use the same hyphens as `SSN_US`. Test those two patterns first, or every ITIN is labeled a Social Security number. `DEA_US` sits inside `MEDICAL_LICENSE_US`. `DL_FL_US` sits inside `DRIVERS_LICENSE_US`. A hyphenated NDC can also be ten digits and sit inside `MEDICAL_NPI_US` when the first digit is 1 or 2. The tighter pattern should win the overlap.

The DEA manual shows the nine-character body. This catalog does not cite a DEA regulation that publishes the pharmacy check-digit procedure, so Fit stays **Strong** on the shape rather than **Check**.

The ABA policy names the ninth routing digit as the check digit. Read the weight formula in that policy before coding it. This page does not copy the weights.

## Canada

A CRA program account is the business number plus a program identifier. Match the full account. The bare 9-digit business number collides with other 9-digit strings, so it is not its own row.

| Proposed key | Identifier | Level | Shape | Fit | Example | Source |
|---|---|---|---|---|---|---|
| `PROGRAM_ACCOUNT_CA` | CRA program account | Federal | 9 digits, a 2-letter program identifier, and 4 digits. Spaces are optional. | Strong | `123456789RT0001` | [CRA program accounts](https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/business-registration/business-number-program-account/need-program-accounts.html) |
| `NAM_QC_CA` | Quebec health-insurance number (NAM) | Province | 4 letters and 8 digits | Strong | `ABCD12345678` | [RAMQ Infolettre 011](https://www.ramq.gouv.qc.ca/SiteCollectionDocuments/professionnels/infolettres/2015/info011-5.pdf) |
| `TVQ_CA_QC` | Quebec TVQ registration | Province | 10 digits, `TQ` or `NR`, and 4 digits | Strong | `1234567890TQ0001` | [Revenu Québec TVQ API](https://www.revenuquebec.ca/fr/services-en-ligne/outils/interface-de-programmation-dapplications-api-servant-a-verifier-la-validite-dun-numero-dinscription-au-fichier-de-la-tvq/), [non-resident `NR` accounts](https://www.revenuquebec.ca/fr/entreprises/taxes/tpstvh-et-tvq/situations-particulieres-liees-a-la-tpstvh-et-a-la-tvq/fournisseurs-hors-quebec/inscription-au-fichier-de-la-tvq-pour-les-fournisseurs-hors-quebec/) |
| `DL_ON_CA` | Ontario driver-licence number | Province | 1 letter and 14 digits. The last two digits are `01`–`31`. | Strong | `A12345678901231` | [Ontario design-system hint](https://designsystem.ontario.ca/components/preview/hint-text.html) |
| `HEALTH_CA_ON` | Ontario health number | Province | 10 digits, first digit `1`–`9`. A photo card adds a 2-letter version code. Some red-and-white cards have no version code or one letter. | Strong with the 2-letter version code; Keyword for 10 digits alone | `1234567890AB` | [OHIP validation schema](https://www.ontario.ca/files/2025-10/moh-ohip-technical-specification-health-card-validation-service-via-electronic-business-services-en-2025-10-08.pdf) |
| `PHN_CA_BC` | British Columbia Personal Health Number | Province | 10 digits, first digit `9`, MOD-11 check digit | Check | `9012372173` | [MSP Teleplan spec, §1.14](https://www2.gov.bc.ca/assets/gov/health/practitioner-pro/medical-services-plan/ch1.pdf) |
| `NEQ_CA_QC` | Quebec enterprise number | Province | 10 digits. The first two are `11` (legal person), `22` (sole proprietorship), `33` (partnership or association), or `88` (public authority). | Keyword | `2200000000` | [NEQ definition](https://www.quebec.ca/entreprises-et-travailleurs-autonomes/demarrer-entreprise/immatriculer-constituer-entreprise/immatriculation-entreprise/numero-entreprise-quebec), [prefix list](https://www.quebec.ca/entreprises-et-travailleurs-autonomes/obtenir-renseignements-entreprise/recherche-registre-entreprises/description-elements-information) |
| `DIN_CA` | Drug Identification Number | Federal | The label prefix `DIN` and 8 digits | Strong | `DIN 00000000` | [Health Canada DIN fact sheet](https://www.canada.ca/en/health-canada/services/drugs-health-products/drug-products/fact-sheets/drug-identification-number.html) |
| `NPN_CA` | Natural Product Number | Federal | The label prefix `NPN` and 8 digits | Strong | `NPN 00000000` | [Health Canada product licensing](https://www.canada.ca/en/health-canada/services/drugs-health-products/natural-non-prescription/applications-submissions/product-licensing.html) |
| `DIN_HM_CA` | Homeopathic medicine number | Federal | The label prefix `DIN-HM` and 8 digits | Strong | `DIN-HM 00000000` | [LNHPD terminology](https://www.canada.ca/en/health-canada/services/drugs-health-products/reports-publications/natural-health-products/licensed-natural-health-products-database-lnhpd-terminology-guide-september-2008.html) |
| `UCI_CA` | IRCC Unique Client Identifier | Federal | 8 digits printed `NNNN-NNNN`, or 10 digits printed `NN-NNNN-NNNN` | Keyword | `00-0000-0000` | [IRCC Help Centre](https://ircc.canada.ca/English/helpcentre/answer.asp?qnum=777&top=4) |

Program identifiers named on the CRA pages cited above:

| Letters | Account |
|---|---|
| `RT` | GST/HST |
| `RP` | Payroll |
| `RC` | Corporation income tax |
| `RM` | Import-export |
| `RZ` | Information returns |
| `RR` | Registered charity |
| `RG` | Air travellers security charge |

The expression should use this list, or a later CRA list, rather than any two letters. CRA's own sample is `123456789 RT 0001`.

`DL_ON_CA` sits inside the current `DRIVERS_LICENSE_CA` pattern. The Ontario pattern should win that overlap. `NAM_QC_CA` does not match `SIN_CA`, because the SIN pattern requires hyphens.

`CUSIP_US_CA` in the United States table is also the Canadian securities identifier. CUSIP Global Services is the national numbering agency for both countries.

### Other provincial and federal health numbers

The Ontario Ministry of Health publishes this chart for client numbers on monitored-drug claims. Quebec and British Columbia are already in the table above with a tighter source. The remaining rows are fixed lengths. A bare run of 8, 9, 10, or 12 digits is not selective, so Fit is **Keyword** unless the row says otherwise.

Source: [Ontario Drug Programs Reference Manual](https://files.ontario.ca/moh-ontario-drug-programs-reference-manual-2023-07-06.pdf), Identifying Numbers Reference Chart (revision of 6 July 2023), section 15.3.

| Proposed key | Issuer | Shape | Fit |
|---|---|---|---|
| `HEALTH_CA_AB` | Alberta | 9 digits | Keyword |
| `HEALTH_CA_MB` | Manitoba | 9 digits | Keyword |
| `HEALTH_CA_NB` | New Brunswick | 9 digits | Keyword |
| `HEALTH_CA_NL` | Newfoundland and Labrador | 12 digits | Keyword |
| `HEALTH_CA_NS` | Nova Scotia | 10 digits | Keyword |
| `HEALTH_CA_NU` | Nunavut | 9 digits | Keyword |
| `HEALTH_CA_NT` | Northwest Territories | 1 letter and 7 digits | Keyword |
| `HEALTH_CA_PE` | Prince Edward Island | 8 digits or 9 digits | Keyword |
| `HEALTH_CA_SK` | Saskatchewan | 9 digits | Keyword |
| `HEALTH_CA_YT` | Yukon | 9 digits | Keyword |
| `HEALTH_CA_CF` | Canadian Forces, as used on those claims | 1 letter and 8 digits | Keyword |

The same chart gives the RCMP client number as 5 or 6 digits, and a First Nations, Inuit, and Aboriginal health number as 8 to 10 digits. Those two are omitted. Five digits are not selective, and a length range is not one format.

The Teleplan specification is the better source for British Columbia: 10 digits, first digit `9`, MOD-11 check. The weights are in §1.14.2 of that PDF. The sample printed there is `9012372173`.

## Mexico

| Proposed key | Identifier | Level | Shape | Fit | Example | Source |
|---|---|---|---|---|---|---|
| `CLABE_MX` | CLABE interbank account key | Federal | 18 digits: 3 bank, 3 plaza, 11 account, 1 control digit | Check | `000000000000000000` | [ABM, how a CLABE is built](https://www.abm.org.mx/preguntas-frecuentes/) |
| `NSS_MX` | IMSS social-security number | Federal | 11 digits | Keyword | `00000000000` | [IMSS procedure 9210-003-200](https://www.imss.gob.mx/sites/all/statics/pdf/procedimientos/9210-003-200.pdf), [affiliation layout](https://www.imss.gob.mx/sites/all/statics/plataformas/downloads/1.Guia%20para%20integrar_movimientos_afiliatorios.pdf) |
| `REGISTRO_PATRONAL_MX` | IMSS employer registry | Federal | 11 characters in the affiliation layout: 10 characters assigned by IMSS, then an 11th digit | Keyword | `A0000000000` | [Same IMSS affiliation layout](https://www.imss.gob.mx/sites/all/statics/plataformas/downloads/1.Guia%20para%20integrar_movimientos_afiliatorios.pdf) |
| `CLAVE_ELECTOR_MX` | INE voter key | Federal | 18 characters, built from surname letters, birth date, sex, state of birth, and an internal homoclave. The cited note lists those elements and does not fix their order. | Keyword | 18 characters | [INE OCR and voter-key sheet](https://sitios.ine.mx/archivos2/tutoriales/sistemas/ApoyoInstitucional/SNR/rsc/docs/PDF/clave_electorOCRcredencialVotar.pdf), [INE classification note](https://transparencia.ine.mx/sistemaot/cargaMasiva/Articulo70/2024/Formato00/UTTYPDP/anl1/resolucion-ct-ot-formato28-3t-2024.pdf) |
| `OCR_INE_MX` | INE credential OCR | Federal | 12 digits (2002 cards) or 13 digits (2008 and 2013 cards) | Keyword | `0000000000000` | [Same INE sheet](https://sitios.ine.mx/archivos2/tutoriales/sistemas/ApoyoInstitucional/SNR/rsc/docs/PDF/clave_electorOCRcredencialVotar.pdf) |
| `PEDIMENTO_MX` | Customs pedimento number | Federal | 15 digits: 2 year, 2 customs office, 4 patent, then 7 digits whose first digit repeats the year. The printed form separates the groups with two spaces and leaves the last 7 digits together. | Strong on the printed groups; Keyword for 15 bare digits | `26  01  0001  1000001` (two spaces between groups) | [SAT Anexo 22 compilation, 2026](https://www.sat.gob.mx/minisitio/NormatividadRMFyRGCE/documentos2026/rgce/compiladas/CompiladoAnexo22_1raRMRGCE2026.pdf) |
| `FOLIO_FISCAL_MX` | CFDI folio fiscal | Federal | 36-character UUID: 8-4-4-4-12 hexadecimal digits | Keyword | `00000000-0000-0000-0000-000000000000` | [SAT Anexo 20](http://omawww.sat.gob.mx/tramitesyservicios/Paginas/anexo_20.htm), [fill guide, 36 positions](http://omawww.sat.gob.mx/tramitesyservicios/Paginas/documentos/Anexo_20_Guia_de_llenado_CFDI.pdf) |

`CLAVE_ELECTOR_MX` needs a keyword, or a position pattern, because a loose 18-character class also matches `CURP_MX`. The INE note lists the elements and the length. It does not publish a position-by-position grammar. Do not ship `[A-Z]{6}…` until an INE specification fixes the order.

The ABM page states that the 18th CLABE digit is a control digit from an algorithm. Read the weights in the ABM or Banxico specification before coding the check. This page does not copy them.

The folio fiscal uses the UUID shape. The same shape appears outside Mexican invoices, which is why Fit is **Keyword**.

## Considered and left out

These are official, and they fail the shape test used above. A later pass can add one when the missing grammar is published.

| Identifier | Why it is not a row |
|---|---|
| CAGE / NCAGE | FAR 52.204-16 defines the code. Five characters are not selective. |
| DUNS | Nine digits. Federal awards stopped using it on 4 April 2022, when the UEI replaced it. |
| CMS Certification Number | Six digits for a Part A provider ([State Operations Manual, ch. 2, §2779A1](https://www.cms.gov/manuals/downloads/som107c02.pdf)). Too short to search for alone. |
| SEVIS ID | [ICE](https://www.ice.gov/sevis/i901/faq) says every SEVIS ID starts with `N`. The cited page does not fix how many digits follow. |
| Most US state driver licences | This pass found a published character grammar for Florida. Other states describe the credential and do not state the character pattern. `DRIVERS_LICENSE_US` remains the broad pattern. |
| Mexican state driver licences | Licensing is state-level. This pass did not find a state specification with one fixed shape. |
| Cédula profesional, clave de centro de trabajo | The credentials exist. This pass did not find a character grammar. |
| RCMP client number, FNIAH number | In the Ontario drug-program chart the RCMP number is 5 or 6 digits, and the FNIAH number is 8 to 10 digits. |

## Keys `"all"` turns on

`DL_FL_US`, `EDD_PAYROLL_US`, `FFL_US`, `N_NUMBER_US`, `HIN_US`, `RTN_US`, `NAM_QC_CA`, `TVQ_QC_CA`, `DL_ON_CA`, `HEALTH_ON_CA`, `PHN_BC_CA`, `NEQ_QC_CA`, `HEALTH_NT_CA`, `HEALTH_CF_CA`, `CUSIP_NNA`, `FOLIO_FISCAL_MX`.

`RTN_US`, `CUSIP_NNA`, and `PHN_BC_CA` are dropped when the check digit fails. `CUSIP_NNA` is included for both `US` and `CA`.

Name `LICENSE_IL_US`, `UEI_US`, `TAXONOMY_US`, `I94_US`, `HEALTH_AB_CA`, `HEALTH_MB_CA`, `HEALTH_NB_CA`, `HEALTH_NU_CA`, `HEALTH_SK_CA`, `HEALTH_YT_CA`, `HEALTH_NL_CA`, `HEALTH_NS_CA`, `HEALTH_PE_CA`, `OCR_INE_MX`, or `REGISTRO_PATRONAL_MX` to load that broader pattern. The anonymizer CLI flag is `--opt-in`.
