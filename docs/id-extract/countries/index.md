# Country catalog

Each page lists the identifiers this package looks for in that country, the type key it emits, a short definition, a synthetic example, and links to the issuing agency or the statute that defines the number.

Pass the ISO-2 code to `extract(..., countries=["AU"])`. `UK` is accepted as `GB`.

Universal identifiers (email, cards, IBAN, …) are documented on [Universal identifiers](../universal.md). They are not repeated here.

| Country | Code | Types |
|---|---|---|
| [Australia](au.md) | `AU` | `ABN_AU`, `TFN_AU`, `DRIVERS_LICENSE_AU` |
| [United States](us.md) | `US` | `SSN_US`, `SSN`, `EIN_US`, `MEDICAL_NPI_US`, `DRIVERS_LICENSE_US`, `MEDICAL_LICENSE_US`, `ITIN_US`, `ATIN_US`, `PTIN_US`, `MBI_US`, `A_NUMBER_US`, `USCIS_RECEIPT_US`, `DOS_CASE_US`, `DEA_US` |
| [Canada](ca.md) | `CA` | `SIN_CA`, `DRIVERS_LICENSE_CA`, `PROGRAM_ACCOUNT_CA`, `DIN_CA`, `NPN_CA`, `DIN_HM_CA`, `UCI_CA` |
| [United Kingdom](gb.md) | `GB` | `NINO_GB`, `VAT_GB`, `COMPANIES_HOUSE_GB`, `DRIVERS_LICENSE_GB` |
| [France](fr.md) | `FR` | `INSEE_FR`, `VAT_FR`, `PASSPORT_FR`, `DRIVERS_LICENSE_FR` |
| [Spain](es.md) | `ES` | `DNI_ES`, `NIE_ES`, `CIF_ES`, `VAT_ES`, `DRIVERS_LICENSE_ES` |
| [Italy](it.md) | `IT` | `CODICE_FISCALE_IT`, `VAT_IT`, `DRIVERS_LICENSE_IT` |
| [India](in.md) | `IN` | `AADHAAR_IN`, `PAN_IN`, `GSTIN_IN`, `DRIVERS_LICENSE_IN` |
| [China](cn.md) | `CN` | `RESIDENT_ID_CN`, `UNIFIED_SOCIAL_CREDIT_CODE_CN`, `PASSPORT_CN` |
| [Germany](de.md) | `DE` | `STEUER_ID_DE`, `VAT_DE`, `PERSONALAUSWEIS_DE`, `DRIVERS_LICENSE_DE` |
| [Japan](jp.md) | `JP` | `MY_NUMBER_JP`, `RESIDENT_CARD_JP`, `DRIVERS_LICENSE_JP` |
| [South Korea](kr.md) | `KR` | `RESIDENT_REGISTRATION_KR`, `BUSINESS_REG_KR` |
| [New Zealand](nz.md) | `NZ` | `IRD_NZ` |
| [Brazil](br.md) | `BR` | `CPF_BR`, `CNPJ_BR`, `RG_BR` |
| [Mexico](mx.md) | `MX` | `CURP_MX`, `RFC_MX`, `CLABE_MX`, `NSS_MX`, `PEDIMENTO_MX` |
| [Argentina](ar.md) | `AR` | `DNI_AR` |
| [South Africa](za.md) | `ZA` | `ID_ZA`, `TAX_ZA` |
| [Singapore](sg.md) | `SG` | `NRIC_SG` |
| [Hong Kong](hk.md) | `HK` | `HKID_HK` |
| [Taiwan](tw.md) | `TW` | `NATIONAL_ID_TW` |
| [Netherlands](nl.md) | `NL` | `BSN_NL`, `VAT_NL` |
| [Belgium](be.md) | `BE` | `NISS_BE` |
| [Switzerland](ch.md) | `CH` | `AHV_CH`, `VAT_CH` |
| [Austria](at.md) | `AT` | `SVNR_AT` |
| [Sweden](se.md) | `SE` | `PERSONAL_ID_SE` |
| [Norway](no.md) | `NO` | `NATIONAL_ID_NO` |
| [Denmark](dk.md) | `DK` | `CPR_DK` |
| [Finland](fi.md) | `FI` | `HETU_FI` |
| [Poland](pl.md) | `PL` | `PESEL_PL` |
| [Ireland](ie.md) | `IE` | `PPS_IE` |
| [Portugal](pt.md) | `PT` | `NIF_PT` |
| [Greece](gr.md) | `GR` | `AMKA_GR` |
| [Israel](il.md) | `IL` | `ID_IL` |
| [Türkiye](tr.md) | `TR` | `NATIONAL_ID_TR` |
| [Russia](ru.md) | `RU` | `PASSPORT_RU` |
| [Thailand](th.md) | `TH` | `NATIONAL_ID_TH` |
| [Malaysia](my.md) | `MY` | `NRIC_MY` |
| [Indonesia](id.md) | `ID` | `NIK_ID` |
