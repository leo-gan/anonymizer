#!/usr/bin/env python3
"""Write docs/id-extract/countries/*.md from the catalog below.

Run from the repository root. Official URLs were checked against
government and standards sites in September 2026.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "id-extract" / "countries"

# Each country: name, types[]. Official links only (agency or statute).
COUNTRIES: dict[str, dict] = {
    "AU": {
        "name": "Australia",
        "types": [
            {
                "key": "ABN_AU",
                "name": "Australian Business Number (ABN)",
                "definition": "An 11-digit number that identifies a business or organisation to the Australian Government and the public. It is issued through the Australian Business Register.",
                "shape": "11 digits, optional spaces as 2 3 3 3",
                "example": "51 824 753 556",
                "checksum": "none in this package (the ABR uses a weighting check the regex does not run)",
                "sources": [
                    (
                        "What an ABN is (ABR)",
                        "https://www.abr.gov.au/business-super-funds-charities/applying-abn",
                    ),
                    (
                        "A New Tax System (Australian Business Number) Act 1999",
                        "https://www.legislation.gov.au/C2004A00467/latest",
                    ),
                    (
                        "ATO — registering for an ABN",
                        "https://www.ato.gov.au/businesses-and-organisations/starting-registering-or-closing-a-business/starting-your-own-business/registration-obligations-for-businesses/registering-for-an-australian-business-number",
                    ),
                ],
            },
            {
                "key": "TFN_AU",
                "name": "Tax File Number (TFN)",
                "definition": "A personal reference number in the Australian tax and superannuation systems. The ATO says it is usually 9 digits and stays with the person for life.",
                "shape": "9 digits, optional spaces as 3 3 3",
                "example": "123 456 789",
                "checksum": "none",
                "sources": [
                    (
                        "ATO — What is a tax file number?",
                        "https://www.ato.gov.au/individuals-and-families/tax-file-number/what-is-a-tax-file-number",
                    ),
                    (
                        "Income Tax Assessment Act 1936 s 202B (TFN application)",
                        "https://www.legislation.gov.au/C1936A00027/latest",
                    ),
                ],
            },
            {
                "key": "DRIVERS_LICENSE_AU",
                "name": "Driver licence (state and territory)",
                "definition": "A licence to drive is issued by each state or territory, not by the Commonwealth. Formats differ. This pattern is a broad 8–10 character token and will over-match.",
                "shape": "8–10 letters or digits",
                "example": "12345678",
                "checksum": "none",
                "sources": [
                    (
                        "National Transport Commission — driver licensing",
                        "https://www.ntc.gov.au/transport-reform/ntc-projects/australian-driver-licensing",
                    ),
                    (
                        "Example issuer: NSW Service — driver licences",
                        "https://www.nsw.gov.au/driving-boating-and-transport/driver-and-rider-licences",
                    ),
                ],
            },
        ],
    },
    "US": {
        "name": "United States",
        "types": [
            {
                "key": "SSN_US",
                "name": "Social Security number (SSN)",
                "definition": "A nine-digit number assigned by the Social Security Administration to record earnings and administer benefits. It is also used as a taxpayer identifier.",
                "shape": "AAA-GG-SSSS",
                "example": "123-45-6789",
                "checksum": "none",
                "sources": [
                    (
                        "SSA — request a Social Security number",
                        "https://www.ssa.gov/number-card/request-number-first-time",
                    ),
                    (
                        "SSA POMS RM 10201.030 — structure of the SSN",
                        "https://secure.ssa.gov/poms.nsf/lnx/0110201030",
                    ),
                    (
                        "Social Security Act",
                        "https://www.ssa.gov/OP_Home/ssact/ssact.htm",
                    ),
                ],
            },
            {
                "key": "SSN",
                "name": "SSN (legacy key)",
                "definition": "Same pattern as SSN_US. Kept so older callers that ask for type SSN still match.",
                "shape": "AAA-GG-SSSS",
                "example": "123-45-6789",
                "checksum": "none",
                "sources": [
                    ("SSA — Social Security numbers", "https://www.ssa.gov/ssnumber/"),
                ],
            },
            {
                "key": "EIN_US",
                "name": "Employer Identification Number (EIN)",
                "definition": "A nine-digit federal tax identifier the IRS assigns to businesses, estates, trusts, and other entities. Form SS-4 is the application.",
                "shape": "NN-NNNNNNN",
                "example": "12-3456789",
                "checksum": "none",
                "sources": [
                    (
                        "IRS — Employer identification number",
                        "https://www.irs.gov/businesses/employer-identification-number",
                    ),
                    (
                        "About Form SS-4",
                        "https://www.irs.gov/forms-pubs/about-form-ss-4",
                    ),
                ],
            },
            {
                "key": "MEDICAL_NPI_US",
                "name": "National Provider Identifier (NPI)",
                "definition": "A 10-digit identifier for covered health-care providers under HIPAA Administrative Simplification. CMS assigns it through NPPES. The number is intelligence-free.",
                "shape": "10 digits",
                "example": "1234567893",
                "checksum": "Luhn over prefix 80840 + the 10 digits (CMS)",
                "sources": [
                    (
                        "CMS — National Provider Identifier Standard",
                        "https://www.cms.gov/regulations-and-guidance/administrative-simplification/nationalprovidentstand",
                    ),
                    (
                        "45 CFR Part 162 (HIPAA unique identifiers)",
                        "https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-162",
                    ),
                ],
            },
            {
                "key": "DRIVERS_LICENSE_US",
                "name": "Driver licence (state)",
                "definition": "Each U.S. state issues its own licence. There is no single federal format. This pattern is deliberately broad.",
                "shape": "1–2 letters + 6–8 digits, or 8–9 digits, or 1 letter + 7–8 digits",
                "example": "D1234567",
                "checksum": "none",
                "sources": [
                    (
                        "AAMVA — driver licensing",
                        "https://www.aamva.org/topics/driver-licensing",
                    ),
                ],
            },
            {
                "key": "MEDICAL_LICENSE_US",
                "name": "Medical or DEA-style licence (structural)",
                "definition": "A coarse pattern for U.S. professional or DEA-style licence tokens. It is not a complete DEA or state-board recognizer.",
                "shape": "1–2 letters + 6–9 digits",
                "example": "AB1234567",
                "checksum": "none",
                "sources": [
                    (
                        "DEA — registration",
                        "https://www.deadiversion.usdoj.gov/drugreg/index.html",
                    ),
                ],
            },
            {
                "key": "ITIN_US",
                "name": "Individual Taxpayer Identification Number (ITIN)",
                "definition": "A tax processing number for a person who needs a U.S. taxpayer identifier and cannot get an SSN. It uses the SSN hyphenation, starts with 9, and the fourth and fifth digits fall in the IRS ranges. A same-span SSN label is dropped.",
                "shape": "9NN-NN-NNNN, middle digits 50–65, 70–88, 90–92, or 94–99",
                "example": "900-70-0000",
                "checksum": "none",
                "sources": [
                    (
                        "IRS — Taxpayer identification numbers",
                        "https://www.irs.gov/tin/taxpayer-identification-numbers-tin",
                    ),
                    (
                        "IRM 3.21.263 — ITIN ranges",
                        "https://www.irs.gov/irm/part3/irm_03-021-263r",
                    ),
                ],
            },
            {
                "key": "ATIN_US",
                "name": "Adoption Taxpayer Identification Number (ATIN)",
                "definition": "A temporary IRS number for a child in a pending domestic adoption. It uses the SSN hyphenation, starts with 9, and the fourth and fifth digits are 93.",
                "shape": "9NN-93-NNNN",
                "example": "900-93-0000",
                "checksum": "none",
                "sources": [
                    (
                        "IRM 3.13.40 — ATIN format",
                        "https://www.irs.gov/irm/part3/irm_03-013-040",
                    ),
                ],
            },
            {
                "key": "PTIN_US",
                "name": "Preparer Tax Identification Number (PTIN)",
                "definition": "The identifier a paid tax return preparer puts on returns they prepare. The IRS describes it as the letter P followed by eight digits.",
                "shape": "P + 8 digits",
                "example": "P00000000",
                "checksum": "none",
                "sources": [
                    (
                        "IRM 3.12.2 — PTIN",
                        "https://www.irs.gov/irm/part3/irm_03-012-002r",
                    ),
                ],
            },
            {
                "key": "MBI_US",
                "name": "Medicare Beneficiary Identifier (MBI)",
                "definition": "The 11-character identifier CMS prints on Medicare cards. Characters 2, 5, 8, and 9 are letters. Letters S, L, O, I, B, and Z are excluded. Dashes on the card are optional in text.",
                "shape": "11 characters, CMS position classes, optional dashes as 4-3-4",
                "example": "1EG4-TE5-MK73",
                "checksum": "none",
                "sources": [
                    (
                        "CMS — MBI format",
                        "https://www.cms.gov/medicare/new-medicare-card/understanding-the-mbi-with-format.pdf",
                    ),
                ],
            },
            {
                "key": "A_NUMBER_US",
                "name": "Alien Registration Number",
                "definition": "The DHS file number for a non-citizen. USCIS describes it as the letter A followed by 7, 8, or 9 digits. A shorter number is padded with zeros in current systems.",
                "shape": "A, optional hyphen, 7–9 digits",
                "example": "A000000001",
                "checksum": "none",
                "sources": [
                    ("USCIS — A-Number", "https://www.uscis.gov/glossary-term/50684"),
                ],
            },
            {
                "key": "USCIS_RECEIPT_US",
                "name": "USCIS receipt number",
                "definition": "The 13-character identifier USCIS assigns to an application or petition: three letters and ten digits.",
                "shape": "3 letters + 10 digits",
                "example": "ABC0000000001",
                "checksum": "none",
                "sources": [
                    (
                        "USCIS — receipt number field",
                        "https://my.uscis.gov/accounts/annual-asylum-fee/questionnaire",
                    ),
                ],
            },
            {
                "key": "DOS_CASE_US",
                "name": "Department of State immigrant case ID",
                "definition": "The case id on an immigrant visa packet. USCIS describes the ordinary form as three letters and 9 or 10 digits, and a Diversity Visa case as four digits, two letters, and five digits. A same-span USCIS receipt wins.",
                "shape": "3 letters + 9 or 10 digits, or 4 digits + 2 letters + 5 digits",
                "example": "XYZ0123456789",
                "checksum": "none",
                "sources": [
                    (
                        "USCIS — A-Number and DOS case ID",
                        "https://www.uscis.gov/forms/filing-fees/uscis-immigrant-fee/immigrant-fee-payment-tips-on-finding-your-a-number-and-dos-case-id",
                    ),
                ],
            },
            {
                "key": "DEA_US",
                "name": "DEA registration number",
                "definition": "The controlled-substance registration number: two letters and seven digits. A hospital may append a hyphen and an internal suffix under 21 CFR 1301.22(c). A same-span medical-licence label is dropped.",
                "shape": "2 letters + 7 digits, optional hyphen and suffix",
                "example": "AB1234567",
                "checksum": "none",
                "sources": [
                    (
                        "DEA Practitioner's Manual",
                        "https://www.deadiversion.usdoj.gov/GDP/%28DEA-DC-071%29%28EO-DEA226%29_Practitioner%27s_Manual_%28final%29.pdf",
                    ),
                    (
                        "21 CFR 1301.22",
                        "https://www.ecfr.gov/current/title-21/chapter-II/part-1301/section-1301.22",
                    ),
                ],
            },
        ],
    },
    "CA": {
        "name": "Canada",
        "types": [
            {
                "key": "SIN_CA",
                "name": "Social Insurance Number (SIN)",
                "definition": "A unique 9-digit number issued by Service Canada. It identifies a person for income tax under Income Tax Act s. 237 and for certain federal programs. Temporary SINs begin with 9.",
                "shape": "NNN-NNN-NNN",
                "example": "046-454-286",
                "checksum": "Luhn",
                "sources": [
                    (
                        "Service Canada — Social Insurance Number",
                        "https://www.canada.ca/en/employment-social-development/services/sin.html",
                    ),
                    (
                        "CRA — SIN on a tax return",
                        "https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/personal-address-information/social-insurance-number.html",
                    ),
                    (
                        "Income Tax Act (Canada)",
                        "https://laws-lois.justice.gc.ca/eng/acts/I-3.3/",
                    ),
                ],
            },
            {
                "key": "DRIVERS_LICENSE_CA",
                "name": "Driver licence (province or territory)",
                "definition": "Licences are issued by each province or territory. Formats vary. The second alternative in the pattern is very broad.",
                "shape": "Letter + grouped digits, or 5–15 alphanumeric",
                "example": "A1234-12345-12345",
                "checksum": "none",
                "sources": [
                    (
                        "Example issuer: Ontario — driver's licence",
                        "https://www.ontario.ca/page/drivers-licence",
                    ),
                ],
            },
            {
                "key": "PROGRAM_ACCOUNT_CA",
                "name": "CRA program account",
                "definition": "The business number plus a program identifier and a four-digit reference. The letters this package accepts are RT, RP, RC, RM, RZ, RR, and RG.",
                "shape": "9 digits + program letters + 4 digits",
                "example": "123456789RT0001",
                "checksum": "none",
                "sources": [
                    (
                        "CRA — program accounts",
                        "https://www.canada.ca/en/revenue-agency/services/tax/businesses/topics/business-registration/business-number-program-account/need-program-accounts.html",
                    ),
                ],
            },
            {
                "key": "DIN_CA",
                "name": "Drug Identification Number (DIN)",
                "definition": "The eight-digit number Health Canada assigns to a drug before it is marketed. The label prints the prefix DIN. The match includes that prefix.",
                "shape": "DIN + 8 digits",
                "example": "DIN 00000000",
                "checksum": "none",
                "sources": [
                    (
                        "Health Canada — DIN",
                        "https://www.canada.ca/en/health-canada/services/drugs-health-products/drug-products/fact-sheets/drug-identification-number.html",
                    ),
                ],
            },
            {
                "key": "NPN_CA",
                "name": "Natural Product Number (NPN)",
                "definition": "The eight-digit licence number on a natural health product. The match includes the prefix NPN.",
                "shape": "NPN + 8 digits",
                "example": "NPN 00000000",
                "checksum": "none",
                "sources": [
                    (
                        "Health Canada — product licensing",
                        "https://www.canada.ca/en/health-canada/services/drugs-health-products/natural-non-prescription/applications-submissions/product-licensing.html",
                    ),
                ],
            },
            {
                "key": "DIN_HM_CA",
                "name": "Homeopathic medicine number (DIN-HM)",
                "definition": "The eight-digit number on a licensed homeopathic medicine. The match includes the prefix DIN-HM.",
                "shape": "DIN-HM + 8 digits",
                "example": "DIN-HM 00000000",
                "checksum": "none",
                "sources": [
                    (
                        "Health Canada — LNHPD terminology",
                        "https://www.canada.ca/en/health-canada/services/drugs-health-products/reports-publications/natural-health-products/licensed-natural-health-products-database-lnhpd-terminology-guide-september-2008.html",
                    ),
                ],
            },
            {
                "key": "UCI_CA",
                "name": "Unique Client Identifier (UCI)",
                "definition": "The client id IRCC prints on its documents. This package matches the 10-digit form NN-NNNN-NNNN. The 8-digit form is omitted because that hyphenation is too common.",
                "shape": "NN-NNNN-NNNN",
                "example": "00-0000-0000",
                "checksum": "none",
                "sources": [
                    (
                        "IRCC — When will I get my UCI?",
                        "https://ircc.canada.ca/English/helpcentre/answer.asp?qnum=777&top=4",
                    ),
                ],
            },
        ],
    },
    "GB": {
        "name": "United Kingdom",
        "alias": "UK is accepted as GB",
        "types": [
            {
                "key": "NINO_GB",
                "name": "National Insurance number",
                "definition": "HMRC uses this number to record National Insurance contributions and tax against one person. GOV.UK describes it as 2 letters, 6 numbers, and a final letter.",
                "shape": "Two prefix letters (not all pairs), 6 digits, optional suffix A/B/C/D/F/M",
                "example": "AB123456C",
                "checksum": "none",
                "sources": [
                    (
                        "GOV.UK — Find your National Insurance number",
                        "https://www.gov.uk/find-national-insurance-number",
                    ),
                    (
                        "GOV.UK — National Insurance",
                        "https://www.gov.uk/national-insurance",
                    ),
                ],
            },
            {
                "key": "VAT_GB",
                "name": "VAT registration number",
                "definition": "The UK VAT number as used after Brexit. Common printed forms are GB plus 9 or 12 digits, or the government-department prefixes GD and HA.",
                "shape": "GB + 9 or 12 digits, or GBGD/GBHA + 3 digits",
                "example": "GB123456789",
                "checksum": "none",
                "sources": [
                    (
                        "GOV.UK — VAT registration numbers",
                        "https://www.gov.uk/vat-registration-numbers",
                    ),
                    (
                        "HMRC — Check a UK VAT number",
                        "https://www.gov.uk/check-uk-vat-number",
                    ),
                ],
            },
            {
                "key": "COMPANIES_HOUSE_GB",
                "name": "Companies House company number",
                "definition": "The registrar’s number for a company. England and Wales companies are usually 8 digits. Scotland and Northern Ireland use prefixes such as SC and NI.",
                "shape": "Optional SC/NI/OC/SO + 6–8 digits",
                "example": "SC123456",
                "checksum": "none",
                "sources": [
                    (
                        "Companies House — get information about a company",
                        "https://www.gov.uk/get-information-about-a-company",
                    ),
                    (
                        "Companies Act 2006",
                        "https://www.legislation.gov.uk/ukpga/2006/46/contents",
                    ),
                ],
            },
            {
                "key": "DRIVERS_LICENSE_GB",
                "name": "Photocard driving licence number",
                "definition": "The 16-character driver number printed on a Great Britain photocard licence.",
                "shape": "16 characters in the DVLA layout",
                "example": "MORGA753116SM9IJ",
                "checksum": "none",
                "sources": [
                    (
                        "GOV.UK — driving licence categories",
                        "https://www.gov.uk/driving-licence-categories",
                    ),
                    (
                        "DVLA",
                        "https://www.gov.uk/government/organisations/driver-and-vehicle-licensing-agency",
                    ),
                ],
            },
        ],
    },
    "FR": {
        "name": "France",
        "types": [
            {
                "key": "INSEE_FR",
                "name": "NIR / numéro de sécurité sociale",
                "definition": "The numéro d’inscription au répertoire (NIR) is the French social-security number. It is issued from the INSEE directory. It usually starts with 1 or 2 (sex) followed by date and place digits. This pattern is simplified for recall.",
                "shape": "1 or 2, then 12–14 more digits",
                "example": "255081416802538",
                "checksum": "none in this package (the official key is mod 97)",
                "sources": [
                    (
                        "Ameli — numéro de sécurité sociale",
                        "https://www.ameli.fr/assure/droits-demarches/principes/numero-securite-sociale",
                    ),
                    (
                        "INSEE — répertoire national d’identification des personnes physiques",
                        "https://www.insee.fr/fr/metadonnees/definition/c1602",
                    ),
                ],
            },
            {
                "key": "VAT_FR",
                "name": "Numéro de TVA intracommunautaire",
                "definition": "France’s intra-Community VAT identifier. Service-Public describes it as FR + a 2-character key + the 9-digit SIREN.",
                "shape": "FR + 2 letters or digits + 9 digits",
                "example": "FRXX123456789",
                "checksum": "none",
                "sources": [
                    (
                        "Service-Public — numéro de TVA intracommunautaire",
                        "https://www.service-public.fr/professionnels-entreprises/vosdroits/F23570",
                    ),
                    (
                        "Council Directive 2006/112/EC (VAT)",
                        "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32006L0112",
                    ),
                ],
            },
            {
                "key": "PASSPORT_FR",
                "name": "French passport number",
                "definition": "A structural pattern for common French passport numbers.",
                "shape": "2 digits + 2 letters + 5 digits",
                "example": "12AB34567",
                "checksum": "none",
                "sources": [
                    (
                        "Service-Public — passeport",
                        "https://www.service-public.fr/particuliers/vosdroits/N360",
                    ),
                    (
                        "ICAO Doc 9303",
                        "https://www.icao.int/publications/pages/publication.aspx?docnum=9303",
                    ),
                ],
            },
            {
                "key": "DRIVERS_LICENSE_FR",
                "name": "Permis de conduire",
                "definition": "A coarse 12-character token for the French driving licence number.",
                "shape": "12 letters or digits",
                "example": "12AB34567890",
                "checksum": "none",
                "sources": [
                    (
                        "Service-Public — permis de conduire",
                        "https://www.service-public.fr/particuliers/vosdroits/N530",
                    ),
                ],
            },
        ],
    },
    "ES": {
        "name": "Spain",
        "types": [
            {
                "key": "DNI_ES",
                "name": "Documento Nacional de Identidad (DNI / NIF)",
                "definition": "The Spanish national identity document. The Ministry of the Interior issues it. The number plus a check letter is the NIF for natural persons.",
                "shape": "8 digits + check letter (not I, Ñ, O, U)",
                "example": "12345678Z",
                "checksum": "remainder modulo 23 → letter table in RD 255/2025 art. 12",
                "sources": [
                    (
                        "Ministerio del Interior — DNI",
                        "https://www.interior.gob.es/opencms/es/servicios-al-ciudadano/tramites-y-gestiones/dni/",
                    ),
                    (
                        "Cálculo del dígito de control del NIF/NIE",
                        "https://www.interior.gob.es/opencms/es/servicios-al-ciudadano/tramites-y-gestiones/dni/calculo-del-digito-de-control-del-nif-nie/",
                    ),
                    (
                        "Normativa básica reguladora del DNI (Interior; includes RD 255/2025 and LO 4/2015)",
                        "https://www.interior.gob.es/opencms/es/servicios-al-ciudadano/tramites-y-gestiones/dni/normativa-basica-reguladora/",
                    ),
                ],
            },
            {
                "key": "NIE_ES",
                "name": "Número de Identidad de Extranjero (NIE)",
                "definition": "The identity number for foreign residents in Spain. It starts with X, Y, or Z, then 7 digits and the same check letter as the DNI.",
                "shape": "X/Y/Z + 7 digits + letter",
                "example": "X1234567L",
                "checksum": "same letter table as DNI after mapping X=0, Y=1, Z=2",
                "sources": [
                    (
                        "Ministerio del Interior — NIF/NIE check digit",
                        "https://www.interior.gob.es/opencms/es/servicios-al-ciudadano/tramites-y-gestiones/dni/calculo-del-digito-de-control-del-nif-nie/",
                    ),
                    (
                        "Ministerio del Interior — extranjería (NIE)",
                        "https://www.interior.gob.es/opencms/es/servicios-al-ciudadano/tramites-y-gestiones/extranjeria/",
                    ),
                ],
            },
            {
                "key": "CIF_ES",
                "name": "Código de Identificación Fiscal (companies)",
                "definition": "The Spanish tax identifier for legal persons. Agencia Tributaria assigns it.",
                "shape": "Letter + 7 digits + letter or digit",
                "example": "A12345674",
                "checksum": "none in this package",
                "sources": [
                    (
                        "Agencia Tributaria — NIF",
                        "https://sede.agenciatributaria.gob.es/Sede/en_gb/todas-gestiones/censos-nif-domicilio-fiscal.html",
                    ),
                ],
            },
            {
                "key": "VAT_ES",
                "name": "Spanish VAT number",
                "definition": "Intra-Community form ES + the national tax identifier.",
                "shape": "ES + 9 alphanumeric",
                "example": "ESA12345674",
                "checksum": "none",
                "sources": [
                    (
                        "VIES — validate a VAT number",
                        "https://ec.europa.eu/taxation_customs/vies/",
                    ),
                ],
            },
            {
                "key": "DRIVERS_LICENSE_ES",
                "name": "Permiso de conducción",
                "definition": "A coarse 9–10 character token for Spanish driving-licence numbers.",
                "shape": "9–10 letters or digits",
                "example": "12345678Z",
                "checksum": "none",
                "sources": [
                    (
                        "DGT — permiso de conducción",
                        "https://www.dgt.es/nuestros-servicios/permisos-de-conducir/",
                    ),
                ],
            },
        ],
    },
    "IT": {
        "name": "Italy",
        "types": [
            {
                "key": "CODICE_FISCALE_IT",
                "name": "Codice fiscale",
                "definition": "The Italian tax code for a natural person. The Agenzia delle Entrate assigns it. Sixteen characters encode name, birth date, place, and a check letter.",
                "shape": "6 letters + 2 digits + letter + 2 digits + letter + 3 digits + letter",
                "example": "RSSMRA85T10A562S",
                "checksum": "odd/even character table, last letter",
                "sources": [
                    (
                        "Agenzia delle Entrate — codice fiscale",
                        "https://www.agenziaentrate.gov.it/portale/web/guest/schede/istanze/richiesta-ts_cf/informazioni-codice-fiscale",
                    ),
                    (
                        "DPR 605/1973 (anagrafe tributaria)",
                        "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:decreto.del.presidente.della.repubblica:1973-09-29;605",
                    ),
                ],
            },
            {
                "key": "VAT_IT",
                "name": "Partita IVA",
                "definition": "Italy’s VAT number in intra-Community form: IT plus 11 digits.",
                "shape": "IT + 11 digits",
                "example": "IT12345678901",
                "checksum": "none in this package",
                "sources": [
                    (
                        "Agenzia delle Entrate — partita IVA",
                        "https://www.agenziaentrate.gov.it/portale/web/guest/schede/istanze/apertura-partita-iva/infogen-apertura-piva",
                    ),
                ],
            },
            {
                "key": "DRIVERS_LICENSE_IT",
                "name": "Patente di guida",
                "definition": "A coarse 10-character token for an Italian driving-licence number.",
                "shape": "10 letters or digits",
                "example": "U1A2345678",
                "checksum": "none",
                "sources": [
                    (
                        "MIT — patente di guida",
                        "https://www.ilportaledellautomobilista.it/",
                    ),
                ],
            },
        ],
    },
    "IN": {
        "name": "India",
        "types": [
            {
                "key": "AADHAAR_IN",
                "name": "Aadhaar",
                "definition": "A 12-digit unique identity number issued by the Unique Identification Authority of India under the Aadhaar Act, 2016. UIDAI states that it is a random number and is not proof of citizenship.",
                "shape": "12 digits, optional spaces as 4 4 4. First digit is not 0 or 1.",
                "example": "2341 2341 2346",
                "checksum": "Verhoeff",
                "sources": [
                    ("UIDAI — Aadhaar", "https://uidai.gov.in/en/my-aadhaar"),
                    (
                        "The Aadhaar (Targeted Delivery of Financial and Other Subsidies, Benefits and Services) Act, 2016",
                        "https://www.indiacode.nic.in/handle/123456789/2154",
                    ),
                    (
                        "UIDAI legal framework",
                        "https://uidai.gov.in/en/about-uidai/legal-framework.html",
                    ),
                ],
            },
            {
                "key": "PAN_IN",
                "name": "Permanent Account Number (PAN)",
                "definition": "A 10-character tax identifier issued by the Income Tax Department. It is used on returns and for specified financial transactions.",
                "shape": "5 letters + 4 digits + 1 letter",
                "example": "ABCDE1234F",
                "checksum": "none",
                "sources": [
                    (
                        "Income Tax Department — PAN",
                        "https://www.incometax.gov.in/iec/foportal/help/individual/return-preparation-help/permanent-account-number-pan",
                    ),
                    (
                        "Income-tax Act, 1961 s. 139A",
                        "https://incometaxindia.gov.in/pages/acts/income-tax-act.aspx",
                    ),
                ],
            },
            {
                "key": "GSTIN_IN",
                "name": "GSTIN",
                "definition": "The Goods and Services Tax Identification Number. It embeds a state code and a PAN.",
                "shape": "2-digit state + PAN + entity + Z + check",
                "example": "27ABCDE1234F1Z5",
                "checksum": "none in this package",
                "sources": [
                    ("GST portal", "https://www.gst.gov.in/"),
                    (
                        "Central Goods and Services Tax Act, 2017",
                        "https://www.indiacode.nic.in/handle/123456789/2276",
                    ),
                ],
            },
            {
                "key": "DRIVERS_LICENSE_IN",
                "name": "Driving licence",
                "definition": "Issued by state transport authorities. The common printed form starts with a two-letter state code.",
                "shape": "State code + 2 digits + 11 digits, or state + hyphen + 13 digits",
                "example": "MH12 20110012345",
                "checksum": "none",
                "sources": [
                    (
                        "Ministry of Road Transport — Parivahan",
                        "https://parivahan.gov.in/parivahan/",
                    ),
                    (
                        "Motor Vehicles Act, 1988",
                        "https://www.indiacode.nic.in/handle/123456789/1798",
                    ),
                ],
            },
        ],
    },
    "CN": {
        "name": "China",
        "types": [
            {
                "key": "RESIDENT_ID_CN",
                "name": "Resident Identity Card number (居民身份证)",
                "definition": "The 18-character number on the PRC Resident Identity Card. The last character is a check digit and may be X. The encoding is specified in GB 11643-1999.",
                "shape": "17 digits + digit or X",
                "example": "11010519491231002X",
                "checksum": "ISO 7064 MOD 11-2 weights from GB 11643",
                "sources": [
                    (
                        "National Immigration Administration — ID cards",
                        "https://www.nia.gov.cn/",
                    ),
                    (
                        "GB 11643-1999 (citizen identification number)",
                        "https://openstd.samr.gov.cn/",
                    ),
                ],
            },
            {
                "key": "UNIFIED_SOCIAL_CREDIT_CODE_CN",
                "name": "Unified Social Credit Code (统一社会信用代码)",
                "definition": "An 18-character code that identifies a legal person or other organisation in China.",
                "shape": "18 letters or digits",
                "example": "91110000MA01234567",
                "checksum": "none in this package",
                "sources": [
                    ("SAMR — unified social credit code", "https://www.samr.gov.cn/"),
                ],
            },
            {
                "key": "PASSPORT_CN",
                "name": "Chinese passport number",
                "definition": "Common ordinary-passport prefixes E, G, or S plus 8 digits.",
                "shape": "E/G/S + 8 digits",
                "example": "E12345678",
                "checksum": "none",
                "sources": [
                    (
                        "National Immigration Administration — passports",
                        "https://www.nia.gov.cn/",
                    ),
                    (
                        "ICAO Doc 9303",
                        "https://www.icao.int/publications/pages/publication.aspx?docnum=9303",
                    ),
                ],
            },
        ],
    },
    "DE": {
        "name": "Germany",
        "types": [
            {
                "key": "STEUER_ID_DE",
                "name": "Steuerliche Identifikationsnummer",
                "definition": "The 11-digit personal tax ID assigned by the Federal Central Tax Office (BZSt). It stays with the person for life.",
                "shape": "11 digits",
                "example": "12345678901",
                "checksum": "none in this package",
                "sources": [
                    (
                        "BZSt — Identifikationsnummer",
                        "https://www.bzst.de/DE/Privatpersonen/SteuerlicheIdentifikationsnummer/steuerlicheidentifikationsnummer_node.html",
                    ),
                    (
                        "§ 139a AO",
                        "https://www.gesetze-im-internet.de/ao_1977/__139a.html",
                    ),
                ],
            },
            {
                "key": "VAT_DE",
                "name": "Umsatzsteuer-Identifikationsnummer",
                "definition": "Germany’s VAT ID: DE plus 9 digits.",
                "shape": "DE + 9 digits",
                "example": "DE123456789",
                "checksum": "none",
                "sources": [
                    (
                        "BZSt — USt-IdNr.",
                        "https://www.bzst.de/DE/Unternehmen/Identifikationsnummern/Umsatzsteuer-Identifikationsnummer/umsatzsteuer-identifikationsnummer_node.html",
                    ),
                ],
            },
            {
                "key": "PERSONALAUSWEIS_DE",
                "name": "Personalausweis / passport number (structural)",
                "definition": "A coarse 9–10 character token for German ID-card or passport numbers.",
                "shape": "9–10 letters or digits",
                "example": "T22000129",
                "checksum": "none",
                "sources": [
                    ("BMI — Personalausweis", "https://www.personalausweisportal.de/"),
                ],
            },
            {
                "key": "DRIVERS_LICENSE_DE",
                "name": "Führerscheinnummer",
                "definition": "A coarse 11–12 character token for a German driving-licence number.",
                "shape": "11–12 letters or digits",
                "example": "B072RRE2I55",
                "checksum": "none",
                "sources": [
                    (
                        "KBA — Fahrerlaubnis",
                        "https://www.kba.de/DE/Themen/ZentraleRegister/FAER/faer_node.html",
                    ),
                ],
            },
        ],
    },
    "JP": {
        "name": "Japan",
        "types": [
            {
                "key": "MY_NUMBER_JP",
                "name": "Individual Number (My Number)",
                "definition": "A 12-digit number assigned to each resident under the Social Security and Tax Number System.",
                "shape": "12 digits, optional spaces as 4 4 4",
                "example": "1234 5678 9012",
                "checksum": "none in this package",
                "sources": [
                    (
                        "Digital Agency — Individual Number",
                        "https://www.digital.go.jp/policies/mynumber",
                    ),
                    (
                        "Act on the Use of Numbers to Identify a Specific Individual in Administrative Procedures",
                        "https://www.japaneselawtranslation.go.jp/en/laws/view/2284",
                    ),
                ],
            },
            {
                "key": "RESIDENT_CARD_JP",
                "name": "Residence card number (structural)",
                "definition": "A coarse pattern for a residence-card serial (two letters + 8 digits).",
                "shape": "2 letters + 8 digits",
                "example": "AB12345678",
                "checksum": "none",
                "sources": [
                    (
                        "Immigration Services Agency — residence card",
                        "https://www.moj.go.jp/isa/applications/procedures/nyuukokukanri10_00007.html",
                    ),
                ],
            },
            {
                "key": "DRIVERS_LICENSE_JP",
                "name": "Driver licence number",
                "definition": "A 12-digit Japanese driving-licence number.",
                "shape": "12 digits",
                "example": "123456789012",
                "checksum": "none",
                "sources": [
                    (
                        "National Police Agency — driver’s licence",
                        "https://www.npa.go.jp/english/index.html",
                    ),
                ],
            },
        ],
    },
    "KR": {
        "name": "South Korea",
        "types": [
            {
                "key": "RESIDENT_REGISTRATION_KR",
                "name": "Resident registration number (주민등록번호)",
                "definition": "The 13-digit number on the Korean resident registration card, usually written with a hyphen after the birth date.",
                "shape": "6 digits + hyphen + 7 digits",
                "example": "900101-1234567",
                "checksum": "none in this package",
                "sources": [
                    (
                        "Ministry of the Interior and Safety — resident registration",
                        "https://www.mois.go.kr/eng/sub/a03/residentRegistration/screen.do",
                    ),
                    (
                        "Resident Registration Act",
                        "https://elaw.klri.re.kr/eng_service/lawView.do?hseq=59940&lang=ENG",
                    ),
                ],
            },
            {
                "key": "BUSINESS_REG_KR",
                "name": "Business registration number (사업자등록번호)",
                "definition": "A 10-digit number assigned by the National Tax Service to a business.",
                "shape": "NNN-NN-NNNNN",
                "example": "123-45-67890",
                "checksum": "none",
                "sources": [
                    (
                        "National Tax Service — business registration",
                        "https://www.nts.go.kr/english/",
                    ),
                ],
            },
        ],
    },
    "NZ": {
        "name": "New Zealand",
        "types": [
            {
                "key": "IRD_NZ",
                "name": "IRD number",
                "definition": "Inland Revenue’s tax identifier for a person or entity. It is 8 or 9 digits, often written with hyphens.",
                "shape": "2–3 digits + 3–4 digits + 3 digits",
                "example": "490-918-50",
                "checksum": "none in this package",
                "sources": [
                    (
                        "Inland Revenue — IRD numbers",
                        "https://www.ird.govt.nz/managing-my-tax/ird-numbers",
                    ),
                    (
                        "Tax Administration Act 1994",
                        "https://www.legislation.govt.nz/act/public/1994/0166/latest/DLM348343.html",
                    ),
                ],
            },
        ],
    },
    "BR": {
        "name": "Brazil",
        "types": [
            {
                "key": "CPF_BR",
                "name": "CPF (Cadastro de Pessoas Físicas)",
                "definition": "The federal tax identifier for a natural person in Brazil. Receita Federal issues it.",
                "shape": "11 digits, often 000.000.000-00",
                "example": "529.982.247-25",
                "checksum": "two mod-11 check digits",
                "sources": [
                    (
                        "Receita Federal — CPF",
                        "https://www.gov.br/receitafederal/pt-br/assuntos/meu-cpf",
                    ),
                ],
            },
            {
                "key": "CNPJ_BR",
                "name": "CNPJ (Cadastro Nacional da Pessoa Jurídica)",
                "definition": "The federal tax identifier for a legal person.",
                "shape": "14 digits, often 00.000.000/0001-00",
                "example": "11.222.333/0001-81",
                "checksum": "none in this package",
                "sources": [
                    (
                        "Receita Federal — CNPJ",
                        "https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/cadastros/cnpj",
                    ),
                ],
            },
            {
                "key": "RG_BR",
                "name": "RG (Registro Geral)",
                "definition": "A state civil-identity number. Formats vary by state. This pattern is structural.",
                "shape": "8 digits plus a check character, optional dots",
                "example": "12.345.678-9",
                "checksum": "none",
                "sources": [
                    (
                        "Gov.br — documentos de identificação",
                        "https://www.gov.br/pt-br/servicos/obter-a-carteira-de-identidade",
                    ),
                ],
            },
        ],
    },
    "MX": {
        "name": "Mexico",
        "types": [
            {
                "key": "CURP_MX",
                "name": "CURP",
                "definition": "Clave Única de Registro de Población. An 18-character code that identifies a person in Mexican federal records.",
                "shape": "4 letters + 6 digits + H/M + 5 letters + alphanumeric + digit",
                "example": "GARC850101HDFRRN09",
                "checksum": "none in this package",
                "sources": [
                    ("Gobierno de México — CURP", "https://www.gob.mx/curp"),
                    ("RENAPO", "https://www.gob.mx/segob/renapo"),
                ],
            },
            {
                "key": "RFC_MX",
                "name": "RFC (Registro Federal de Contribuyentes)",
                "definition": "The federal tax identifier issued by the SAT. Natural persons use 13 characters; legal persons use 12.",
                "shape": "3–4 letters + 6 digits + 3 alphanumeric",
                "example": "XAXX010101000",
                "checksum": "none",
                "sources": [
                    (
                        "SAT — RFC",
                        "https://www.sat.gob.mx/tramites/operacion/28753/obten-tu-rfc-con-la-clave-unica-de-registro-de-poblacion-curp",
                    ),
                ],
            },
            {
                "key": "CLABE_MX",
                "name": "CLABE",
                "definition": "The 18-digit interbank account key: 3 bank digits, 3 plaza digits, 11 account digits, and a control digit. A failed control digit is dropped.",
                "shape": "18 digits",
                "example": "000000000000000000",
                "checksum": "weights 3, 7, 1 on the first 17 digits",
                "sources": [
                    (
                        "ABM — how a CLABE is built",
                        "https://www.abm.org.mx/preguntas-frecuentes/",
                    ),
                ],
            },
            {
                "key": "NSS_MX",
                "name": "IMSS social-security number (NSS)",
                "definition": "The 11-digit number IMSS assigns to a person. It is permanent. Any standalone 11-digit run matches, so this pattern is broad.",
                "shape": "11 digits",
                "example": "00000000000",
                "checksum": "none",
                "sources": [
                    (
                        "IMSS procedure 9210-003-200",
                        "https://www.imss.gob.mx/sites/all/statics/pdf/procedimientos/9210-003-200.pdf",
                    ),
                ],
            },
            {
                "key": "PEDIMENTO_MX",
                "name": "Customs pedimento number",
                "definition": "The 15-digit customs declaration number from SAT Anexo 22. The printed form separates the year, customs office, and patent with two spaces and leaves the last seven digits together.",
                "shape": "2 digits, two spaces, 2 digits, two spaces, 4 digits, two spaces, 7 digits",
                "example": "26  01  0001  6000001",
                "checksum": "none",
                "sources": [
                    (
                        "SAT Anexo 22 (2026 compilation)",
                        "https://www.sat.gob.mx/minisitio/NormatividadRMFyRGCE/documentos2026/rgce/compiladas/CompiladoAnexo22_1raRMRGCE2026.pdf",
                    ),
                ],
            },
        ],
    },
    "AR": {
        "name": "Argentina",
        "types": [
            {
                "key": "DNI_AR",
                "name": "DNI (Documento Nacional de Identidad)",
                "definition": "The Argentine national identity number. RENAPER issues the document. This pattern is 8 digits only and will over-match.",
                "shape": "8 digits",
                "example": "12345678",
                "checksum": "none",
                "sources": [
                    (
                        "RENAPER / Mi Argentina — DNI",
                        "https://www.argentina.gob.ar/interior/renaper/dni",
                    ),
                    (
                        "Ley 17.671 (identificación, registro y clasificación del potencial humano nacional)",
                        "https://www.argentina.gob.ar/normativa/nacional/ley-17671-21708",
                    ),
                ],
            },
        ],
    },
    "ZA": {
        "name": "South Africa",
        "types": [
            {
                "key": "ID_ZA",
                "name": "South African ID number",
                "definition": "A 13-digit number on the green bar-coded ID or the smart ID card. The first six digits are the date of birth.",
                "shape": "13 digits",
                "example": "8001015009087",
                "checksum": "none in this package (Luhn is used officially)",
                "sources": [
                    (
                        "Department of Home Affairs — ID documents",
                        "https://www.dha.gov.za/index.php/civic-services/identity-documents",
                    ),
                    (
                        "Identification Act 68 of 1997",
                        "https://www.gov.za/documents/identification-act",
                    ),
                ],
            },
            {
                "key": "TAX_ZA",
                "name": "SARS tax reference (structural)",
                "definition": "A 10-digit token used as a coarse match for a SARS tax reference number.",
                "shape": "10 digits",
                "example": "0123456789",
                "checksum": "none",
                "sources": [
                    (
                        "SARS — tax reference number",
                        "https://www.sars.gov.za/individuals/how-to-register-for-tax/",
                    ),
                ],
            },
        ],
    },
    "SG": {
        "name": "Singapore",
        "types": [
            {
                "key": "NRIC_SG",
                "name": "NRIC / FIN",
                "definition": "The National Registration Identity Card number for citizens and PRs (prefix S, T) or the Foreign Identification Number (prefix F, G, M). This pattern covers S, G, and T.",
                "shape": "S/G/T + 7 digits + letter",
                "example": "S1234567D",
                "checksum": "none in this package",
                "sources": [
                    ("ICA — NRIC", "https://www.ica.gov.sg/documents/nric"),
                    (
                        "National Registration Act 1965",
                        "https://sso.agc.gov.sg/Act/NRA1965",
                    ),
                ],
            },
        ],
    },
    "HK": {
        "name": "Hong Kong",
        "types": [
            {
                "key": "HKID_HK",
                "name": "Hong Kong Identity Card number",
                "definition": "The number on the HKID. One or two letters, six digits, and a check digit in parentheses in print (here the last character is the check).",
                "shape": "1–2 letters + 6 digits + 0–9 or A",
                "example": "A1234563",
                "checksum": "none in this package",
                "sources": [
                    (
                        "Immigration Department — HKID",
                        "https://www.immd.gov.hk/eng/services/hkid.html",
                    ),
                    (
                        "Registration of Persons Ordinance (Cap. 177)",
                        "https://www.elegislation.gov.hk/hk/cap177",
                    ),
                ],
            },
        ],
    },
    "TW": {
        "name": "Taiwan",
        "types": [
            {
                "key": "NATIONAL_ID_TW",
                "name": "National ID number (身分證字號)",
                "definition": "A 10-character number: one letter (place of registration) plus 9 digits.",
                "shape": "1 letter + 9 digits",
                "example": "A123456789",
                "checksum": "none in this package",
                "sources": [
                    (
                        "Ministry of the Interior — household registration",
                        "https://www.ris.gov.tw/app/en",
                    ),
                ],
            },
        ],
    },
    "NL": {
        "name": "Netherlands",
        "types": [
            {
                "key": "BSN_NL",
                "name": "Burgerservicenummer (BSN)",
                "definition": "The citizen service number. The Dutch government uses it in dealings with a person. It is 9 digits.",
                "shape": "9 digits",
                "example": "123456782",
                "checksum": "none in this package (11-proef is official)",
                "sources": [
                    (
                        "Rijksoverheid — BSN",
                        "https://www.rijksoverheid.nl/onderwerpen/privacy-en-persoonsgegevens/burgerservicenummer-bsn",
                    ),
                    (
                        "Wet algemene bepalingen burgerservicenummer",
                        "https://wetten.overheid.nl/BWBR0022428",
                    ),
                ],
            },
            {
                "key": "VAT_NL",
                "name": "Dutch VAT number",
                "definition": "NL + 9 digits + B + 2-digit establishment.",
                "shape": "NL#########B##",
                "example": "NL123456789B01",
                "checksum": "none",
                "sources": [
                    (
                        "Belastingdienst — btw-identificatienummer",
                        "https://www.belastingdienst.nl/wps/wcm/connect/bldcontentnl/belastingdienst/zakelijk/btw/administratie_bijhouden/btw-nummers/",
                    ),
                ],
            },
        ],
    },
    "BE": {
        "name": "Belgium",
        "types": [
            {
                "key": "NISS_BE",
                "name": "NISS / numéro de registre national",
                "definition": "The Belgian national register number (also called NISS in social security). Eleven digits, often printed with dots and a hyphen.",
                "shape": "YY.MM.DD-NNN.CC or 11 digits",
                "example": "85.07.30-123.45",
                "checksum": "none in this package",
                "sources": [
                    (
                        "FPS Interior — National Register",
                        "https://www.ibz.rrn.fgov.be/en/national-register/",
                    ),
                    (
                        "Crossroads Bank for Social Security — NISS",
                        "https://www.ksz-bcss.fgov.be/en",
                    ),
                ],
            },
        ],
    },
    "CH": {
        "name": "Switzerland",
        "types": [
            {
                "key": "AHV_CH",
                "name": "AHV / AVS number (13 digits, 756…)",
                "definition": "The Swiss social-security number. Since 2008 it is a 13-digit number that starts with 756 (the ISO country code).",
                "shape": "756.XXXX.XXXX.XX or 756 + 10 digits",
                "example": "756.1234.5678.97",
                "checksum": "none in this package",
                "sources": [
                    (
                        "AHV/AVS — new insurance number",
                        "https://www.ahv-iv.ch/en/Social-insurances/Old-age-and-survivors-insurance-OASI/Insurance-number",
                    ),
                    (
                        "Federal Act on Old-Age and Survivors’ Insurance (AHVG)",
                        "https://www.fedlex.admin.ch/eli/cc/63/837_843_843/en",
                    ),
                ],
            },
            {
                "key": "VAT_CH",
                "name": "Swiss UID / VAT (CHE…)",
                "definition": "The enterprise identification number used as a VAT number, often written CHE followed by 9 digits and MWST, TVA, or IVA.",
                "shape": "CHE + 9 digits + optional MWST/TVA/IVA",
                "example": "CHE123456789MWST",
                "checksum": "none",
                "sources": [
                    ("UID-Register", "https://www.uid.admin.ch/"),
                    (
                        "Federal Act on the Business Identification Number",
                        "https://www.fedlex.admin.ch/eli/cc/2010/614/en",
                    ),
                ],
            },
        ],
    },
    "AT": {
        "name": "Austria",
        "types": [
            {
                "key": "SVNR_AT",
                "name": "Sozialversicherungsnummer",
                "definition": "The Austrian social-insurance number. Ten digits; the last six encode the date of birth.",
                "shape": "10 digits",
                "example": "1237010180",
                "checksum": "none in this package",
                "sources": [
                    (
                        "ÖGK — Sozialversicherungsnummer",
                        "https://www.gesundheitskasse.at/cdscontent/?contentid=10007.821578",
                    ),
                    (
                        "ASVG",
                        "https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=10008147",
                    ),
                ],
            },
        ],
    },
    "SE": {
        "name": "Sweden",
        "types": [
            {
                "key": "PERSONAL_ID_SE",
                "name": "Personnummer",
                "definition": "The Swedish personal identity number. Ten or twelve digits with a hyphen before the last four.",
                "shape": "6 or 8 digits + hyphen + 4 digits",
                "example": "811228-9874",
                "checksum": "none in this package (Luhn is official)",
                "sources": [
                    (
                        "Skatteverket — personal identity number",
                        "https://skatteverket.se/servicelankar/otherlanguages/inenglish/individualsandemployees/livinginsweden/personalidentitynumberandcoordinationnumber.4.2cf1b5cd163796a5c8b4295.html",
                    ),
                    (
                        "Folkbokföringslag (1991:481)",
                        "https://www.riksdagen.se/sv/dokument-och-lagar/dokument/svensk-forfattningssamling/folkbokforingslag-1991481_sfs-1991-481/",
                    ),
                ],
            },
        ],
    },
    "NO": {
        "name": "Norway",
        "types": [
            {
                "key": "NATIONAL_ID_NO",
                "name": "Fødselsnummer",
                "definition": "The Norwegian national identity number. Eleven digits: date of birth plus an individual number and two check digits.",
                "shape": "11 digits",
                "example": "01018012345",
                "checksum": "none in this package",
                "sources": [
                    (
                        "Skatteetaten — national identity number",
                        "https://www.skatteetaten.no/en/person/national-registry/identitetsnummer/fodselsnummer/",
                    ),
                    (
                        "Folkeregisterloven",
                        "https://lovdata.no/dokument/NL/lov/2016-12-09-88",
                    ),
                ],
            },
        ],
    },
    "DK": {
        "name": "Denmark",
        "types": [
            {
                "key": "CPR_DK",
                "name": "CPR-nummer",
                "definition": "The Danish civil-registration number. Ten digits with a hyphen: DDMMYY-XXXX.",
                "shape": "6 digits + hyphen + 4 digits",
                "example": "010180-1234",
                "checksum": "none",
                "sources": [
                    (
                        "CPR Office — civil registration number",
                        "https://cpr.dk/english/civil-registration-number",
                    ),
                    ("CPR-loven", "https://www.retsinformation.dk/eli/lta/2023/1297"),
                ],
            },
        ],
    },
    "FI": {
        "name": "Finland",
        "types": [
            {
                "key": "HETU_FI",
                "name": "Henkilötunnus",
                "definition": "The Finnish personal identity code. Date of birth, a century sign (+, -, or A), an individual number, and a check character.",
                "shape": "DDMMYY + +|-|A + 3 digits + alphanumeric",
                "example": "131052-308T",
                "checksum": "none in this package",
                "sources": [
                    (
                        "Digital and Population Data Services Agency — personal identity code",
                        "https://dvv.fi/en/personal-identity-code",
                    ),
                    (
                        "Laki väestötietojärjestelmästä",
                        "https://www.finlex.fi/fi/laki/ajantasa/2009/20090661",
                    ),
                ],
            },
        ],
    },
    "PL": {
        "name": "Poland",
        "types": [
            {
                "key": "PESEL_PL",
                "name": "PESEL",
                "definition": "The Polish national identification number. Eleven digits encode birth date, serial, sex, and a check digit.",
                "shape": "11 digits",
                "example": "44051401359",
                "checksum": "weighted digits, last is the check",
                "sources": [
                    (
                        "gov.pl — PESEL",
                        "https://www.gov.pl/web/gov/czym-jest-numer-pesel",
                    ),
                    (
                        "Ustawa o ewidencji ludności",
                        "https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20100002171",
                    ),
                ],
            },
        ],
    },
    "IE": {
        "name": "Ireland",
        "types": [
            {
                "key": "PPS_IE",
                "name": "PPS Number",
                "definition": "The Personal Public Service Number. Used for social welfare, tax, and public services in Ireland. Common form is 7 digits plus a letter.",
                "shape": "7 digits + A–W",
                "example": "1234567T",
                "checksum": "none",
                "sources": [
                    (
                        "Gov.ie — PPS Number",
                        "https://www.gov.ie/en/service/12e6de-get-a-personal-public-service-pps-number/",
                    ),
                    (
                        "Social Welfare Consolidation Act 2005",
                        "https://www.irishstatutebook.ie/eli/2005/act/26/enacted/en/html",
                    ),
                ],
            },
        ],
    },
    "PT": {
        "name": "Portugal",
        "types": [
            {
                "key": "NIF_PT",
                "name": "NIF (Número de Identificação Fiscal)",
                "definition": "The Portuguese tax identification number. Nine digits.",
                "shape": "9 digits",
                "example": "123456789",
                "checksum": "none in this package",
                "sources": [
                    (
                        "Autoridade Tributária — NIF",
                        "https://www.portaldasfinancas.gov.pt/at/html/index.html",
                    ),
                ],
            },
        ],
    },
    "GR": {
        "name": "Greece",
        "types": [
            {
                "key": "AMKA_GR",
                "name": "AMKA",
                "definition": "The Greek social-security number (Αριθμός Μητρώου Κοινωνικής Ασφάλισης). Eleven digits.",
                "shape": "11 digits",
                "example": "01018001234",
                "checksum": "none",
                "sources": [
                    ("AMKA official site", "https://www.amka.gr/"),
                ],
            },
        ],
    },
    "IL": {
        "name": "Israel",
        "types": [
            {
                "key": "ID_IL",
                "name": "Teudat Zehut number",
                "definition": "The 9-digit number on the Israeli identity card.",
                "shape": "9 digits",
                "example": "123456782",
                "checksum": "none in this package (Luhn is official)",
                "sources": [
                    (
                        "Population and Immigration Authority — identity card",
                        "https://www.gov.il/en/departments/population_and_immigration_authority",
                    ),
                ],
            },
        ],
    },
    "TR": {
        "name": "Türkiye",
        "types": [
            {
                "key": "NATIONAL_ID_TR",
                "name": "T.C. Kimlik No",
                "definition": "The 11-digit Republic of Türkiye identity number.",
                "shape": "11 digits",
                "example": "10000000146",
                "checksum": "none in this package",
                "sources": [
                    ("NVI — identity card", "https://www.nvi.gov.tr/"),
                    (
                        "Population Services Law No. 5490",
                        "https://www.mevzuat.gov.tr/mevzuat?MevzuatNo=5490&MevzuatTur=1&MevzuatTertip=5",
                    ),
                ],
            },
        ],
    },
    "RU": {
        "name": "Russia",
        "types": [
            {
                "key": "PASSPORT_RU",
                "name": "Internal passport series and number",
                "definition": "The series (4 digits) and number (6 digits) of the internal passport of a citizen of the Russian Federation.",
                "shape": "2 digits + optional space + 2 digits + optional space + 6 digits",
                "example": "45 16 123456",
                "checksum": "none",
                "sources": [
                    (
                        "МВД — паспорт гражданина РФ",
                        "https://мвд.рф/mvd/structure1/Glavnie_upravlenija/guvm",
                    ),
                    (
                        "Federal Law No. 114-FZ (exit/entry) and Government passport statute",
                        "http://pravo.gov.ru/",
                    ),
                ],
            },
        ],
    },
    "TH": {
        "name": "Thailand",
        "types": [
            {
                "key": "NATIONAL_ID_TH",
                "name": "Thai national ID number",
                "definition": "A 13-digit number on the Thai national identity card.",
                "shape": "13 digits",
                "example": "1234567890121",
                "checksum": "none in this package",
                "sources": [
                    (
                        "Department of Provincial Administration — ID card",
                        "https://www.dopa.go.th/",
                    ),
                ],
            },
        ],
    },
    "MY": {
        "name": "Malaysia",
        "types": [
            {
                "key": "NRIC_MY",
                "name": "MyKad / NRIC number",
                "definition": "The 12-digit Malaysian identity-card number, written YYMMDD-PB-###G.",
                "shape": "6 digits + hyphen + 2 digits + hyphen + 4 digits",
                "example": "900101-14-5678",
                "checksum": "none",
                "sources": [
                    (
                        "JPN — MyKad",
                        "https://www.jpn.gov.my/en/core-business/identity-card",
                    ),
                    ("National Registration Act 1959", "https://lom.agc.gov.my/"),
                ],
            },
        ],
    },
    "ID": {
        "name": "Indonesia",
        "types": [
            {
                "key": "NIK_ID",
                "name": "NIK (Nomor Induk Kependudukan)",
                "definition": "The 16-digit population-administration number on the Indonesian KTP.",
                "shape": "16 digits",
                "example": "3174010101900001",
                "checksum": "none",
                "sources": [
                    (
                        "Dukcapil / Kemendagri — NIK",
                        "https://www.dukcapil.kemendagri.go.id/",
                    ),
                    (
                        "Undang-Undang Nomor 24 Tahun 2013 tentang Administrasi Kependudukan",
                        "https://peraturan.bpk.go.id/Details/38852",
                    ),
                ],
            },
        ],
    },
}


HEADER = """# {name} (`{code}`)

National-ID patterns loaded when you pass `countries=["{code}"]` (or `"all"`). Universal patterns always stay.

{alias}

!!! warning "This is a detector, not a legal opinion"
    `id-extract` matches the **shape** of these numbers. A hit is not proof that the value was issued, is still valid, or that the cited statute applies to your document. Checksums, where present, only test the extra digit.

"""


def render_country(code: str, data: dict) -> str:
    alias = ""
    if data.get("alias"):
        alias = f"`{data['alias']}`.\n"
    parts = [HEADER.format(name=data["name"], code=code, alias=alias)]
    for item in data["types"]:
        sources = "\n".join(f"- [{title}]({url})" for title, url in item["sources"])
        parts.append(
            f"## `{item['key']}` — {item['name']}\n\n"
            f"{item['definition']}\n\n"
            f"| | |\n|---|---|\n"
            f"| **Package type** | `{item['key']}` |\n"
            f"| **Shape this package looks for** | {item['shape']} |\n"
            f"| **Checksum** | {item['checksum']} |\n"
            f"| **Example (synthetic)** | `{item['example']}` |\n\n"
            f"**Official sources**\n\n{sources}\n"
        )
    parts.append(
        "The example values are synthetic or well-known public test numbers. "
        "Do not treat them as issued identifiers.\n"
    )
    return "\n".join(parts)


def render_index() -> str:
    rows = []
    for code, data in COUNTRIES.items():
        keys = ", ".join(f"`{t['key']}`" for t in data["types"])
        rows.append(f"| [{data['name']}]({code.lower()}.md) | `{code}` | {keys} |")
    body = "\n".join(rows)
    return f"""# Country catalog

Each page lists the identifiers this package looks for in that country, the type key it emits, a short definition, a synthetic example, and links to the issuing agency or the statute that defines the number.

Pass the ISO-2 code to `extract(..., countries=["AU"])`. `UK` is accepted as `GB`.

Universal identifiers (email, cards, IBAN, …) are documented on [Universal identifiers](../universal.md). They are not repeated here.

| Country | Code | Types |
|---|---|---|
{body}
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.md").write_text(render_index(), encoding="utf-8")
    for code, data in COUNTRIES.items():
        path = OUT / f"{code.lower()}.md"
        path.write_text(render_country(code, data), encoding="utf-8")
        print("wrote", path.relative_to(ROOT))
    missing = set()
    src = ROOT / "packages" / "id-extract" / "src" / "id_extract" / "countries"
    for py in src.glob("*.py"):
        if py.name in {"__init__.py", "universal.py"}:
            continue
        code = py.stem.upper()
        if code not in COUNTRIES:
            missing.add(code)
    if missing:
        raise SystemExit(f"missing country pages: {sorted(missing)}")
    print("countries", len(COUNTRIES))


if __name__ == "__main__":
    main()
