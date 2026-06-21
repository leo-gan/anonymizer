"""Central configuration, defaults, profiles, and model/provider enums.

This module defines:
- Default constants and directories used by the anonymizer.
- Three built-in ConfigProfiles (best-quality, best-speed, best-cost) that
  bundle sensible combinations of model, prompt, chunk size, retries, etc.
- The AppConfig Pydantic model.
- get_config_for_profile() helper (used heavily by the CLI).
- Legacy enums (PromptEnum, ModelName, etc.) for compatibility and
  dynamic provider/model resolution.
"""

from enum import Enum
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel, Field

# Constants that were previously hardcoded in various places
DEFAULT_CHARACTERS_TO_ANONYMIZE: int = 100000
DEFAULT_PROMPT_NAME: str = "detailed"
DEFAULT_MODEL_NAME: str = "gemini-2.5-flash"
DEFAULT_CHUNK_OVERLAP: int = 1000

# Directories and file paths
DEFAULT_ANONYMIZED_DIR: str = "data/anonymized"
DEFAULT_MAPPINGS_DIR: str = "data/mappings"
DEFAULT_DEANONYMIZED_DIR: str = "data/deanonymized"
DEFAULT_STATS_DIR: str = "data/stats"
DEFAULT_CACHE_DIR: str = "data/cache"
DEFAULT_CACHE_FILE: str = "llm_responses.json"
DEFAULT_LOG_FILE: str = "app.log"

# Default Regex Patterns for first-stage NER (hybrid pipeline)
#
# Powered by the RE2 engine (via the "google-re2" package) for linear-time matching,
# guaranteed safety against catastrophic backtracking (ReDoS), and Unicode-friendly
# performance on large documents.
#
# DESIGN:
# - Patterns are intentionally structural (not full checksum validation like Luhn or
#   IBAN mod-97) because pure regex cannot perform arbitrary arithmetic. The fast regex
#   stage is a high-recall filter; the subsequent LLM stage provides semantic validation
#   and catches context-dependent or missed PII.
# - Entity type keys use UPPER_SNAKE_CASE. Country-specific patterns are partitioned
#   using ISO 3166-1 alpha-2 suffixes (e.g. SSN_US, NINO_GB, INSEE_FR, AADHAAR_IN,
#   RESIDENT_ID_CN). This makes it trivial for callers to select a country subset:
#       {k: v for k, v in DEFAULT_REGEX_PATTERNS.items()
#        if not k.endswith(("_US", "_CA", ...)) or k.endswith("_US")}
# - Universal patterns (EMAIL, CREDIT_CARD, IBAN, VIN, IPV4_ADDRESS, etc.) apply
#   globally and are always included.
# - All patterns are RE2-compatible (no look-around assertions, no Python-specific
#   backrefs or recursive patterns). Word boundaries \b are used for many to reduce
#   partial matches inside larger tokens.
# - Backward compatibility: the original five keys (EMAIL, PHONE, SSN, CREDIT_CARD,
#   IP_ADDRESS) continue to exist with improved or equivalent patterns.
#
# COVERAGE (30+ countries, mandatory highlighted):
#   Mandatory: US, CA, GB, ES, IT, FR, IN, CN
#   Additional: DE, JP, KR, AU, NZ, BR, MX, AR, ZA, SG, HK, TW, NL, BE, CH, AT, SE,
#               NO, DK, FI, PL, IE, PT, GR, IL, TR, RU, TH, MY, ID
#
# SUPPORTED PII CATEGORIES (selected highlights):
#   - Communication: EMAIL, PHONE, URL
#   - Network / device: IPV4_ADDRESS (and legacy IP_ADDRESS), IPV6_ADDRESS, MAC_ADDRESS
#   - Financial: CREDIT_CARD, CURRENCY_AMOUNT, CRYPTO_BTC, CRYPTO_ETH, IBAN, BIC_SWIFT,
#     BANK_ACCOUNT_* (selected countries)
#   - Transport / asset: VIN
#   - Temporal: DATE_ISO (common machine / log formats)
#   - National / tax / gov IDs: SSN_* / SIN_* / NINO_* / INSEE_* / AADHAAR_* / RESIDENT_ID_* /
#     DNI_* / NIE_* / CODICE_FISCALE_* / PAN_* / GSTIN_* / USCC_* / STEUER_ID_* / VAT_* etc.
#   - Licenses / permits: DRIVERS_LICENSE_*, MEDICAL_NPI (US), etc.
#   - Business identifiers: EIN_*, VAT_*, CIF_*, COMPANIES_HOUSE_*, BUSINESS_REG_* etc.
#
# You may supply a completely custom dict (or a filtered subset of this one) via the
# `regex_patterns` argument to anonymize_file(). Keys become the entity TYPE in the
# hybrid results and in generated placeholders (e.g. IBAN_3, SSN_US_1, CRYPTO_ETH_2).
#
# See regex_ner.extract_entities_via_regex and the project Recipes / Architecture docs
# for usage and how regex matches are merged with LLM detections.
DEFAULT_REGEX_PATTERNS: Dict[str, str] = {
    # ---------- UNIVERSAL / CROSS-BORDER ----------
    "EMAIL": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
    "PHONE": r"\+?\b(?:\d{1,4}[- \s]?)?\(?\d{2,4}\)?[- \s]?\d{3,4}(?:[- \s]?\d{3,9})?\b",
    "URL": r"\bhttps?://[a-zA-Z0-9.-]+(?:/[^\s<>\"']*)?\b",
    # Legacy key kept for backward compatibility; value identical to IPV4_ADDRESS
    "IP_ADDRESS": r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
    "IPV4_ADDRESS": r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
    "IPV6_ADDRESS": r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|\b(?:[0-9a-fA-F]{1,4}:){1,7}:\b|\b(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}\b",
    "MAC_ADDRESS": r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b",
    # Credit cards (structural, any issuer): 13-19 digits with common separators
    "CREDIT_CARD": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{1,7}\b|\b\d{4}[-\s]?\d{6}[-\s]?\d{5}\b",
    "CURRENCY_AMOUNT": r"\b(?:USD|EUR|GBP|JPY|CNY|INR|CAD|AUD|CHF|SEK|NOK|DKK|ZAR)\s+\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?\b|\b(?:USD|EUR|GBP|JPY|CNY|INR|CAD|AUD|CHF|SEK|NOK|DKK|ZAR)?\s?[\$€£¥₹₩₽]\s?\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?\b|\b\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?\s?(?:USD|EUR|GBP|JPY|CNY|INR|CAD)\b",
    "CRYPTO_BTC": r"\b(?:[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-zA-HJ-NP-Z0-9]{39,59})\b",
    "CRYPTO_ETH": r"\b0x[a-fA-F0-9]{40}\b",
    # IBAN (used in 80+ countries including FR, DE, ES, IT, NL, GB, CH, etc.)
    "IBAN": r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b",
    "BIC_SWIFT": r"\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?\b",
    "VIN": r"\b[A-HJ-NPR-Z0-9]{17}\b",
    # Common machine / log / API date-time formats (ISO-8601 and close variants)
    "DATE_ISO": r"\b\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})?)?\b",

    # ---------- UNITED STATES (US) ----------
    "SSN_US": r"\b\d{3}-\d{2}-\d{4}\b",
    "EIN_US": r"\b\d{2}-\d{7}\b",  # Employer Identification Number / US tax ID for businesses
    "US_PASSPORT": r"\b[A-Z][0-9]{8}\b|\b[0-9]{9}\b",
    # Broad structural patterns for many US state DL formats (over-inclusive by design for recall)
    "DRIVERS_LICENSE_US": r"\b[A-Z]{1,2}\d{6,8}\b|\b\d{8,9}\b|\b[A-Z]\d{7,8}\b",
    "MEDICAL_NPI_US": r"\b[0-9]{10}\b",  # National Provider Identifier (10 digits)
    # Medical / DEA style controlled substance license (example structural)
    "MEDICAL_LICENSE_US": r"\b[A-Z]{1,2}\d{6,9}\b",

    # ---------- CANADA (CA) ----------
    "SIN_CA": r"\b\d{3}-\d{3}-\d{3}\b",  # Social Insurance Number
    "CA_PASSPORT": r"\b[A-Z]{2}\d{6}\b",
    "DRIVERS_LICENSE_CA": r"\b[A-Z]\d{4,5}-\d{5,6}-\d{5}\b|\b[A-Z0-9]{5,15}\b",  # varies by province

    # ---------- UNITED KINGDOM (GB) ----------
    "NINO_GB": r"\b[A-CEGHJ-PR-TW-Z]{1}[A-CEGHJ-NPR-TW-Z]{1}\d{6}[A-DFM]?\b",  # National Insurance Number
    "GB_PASSPORT": r"\b[0-9]{9}\b",
    "DRIVERS_LICENSE_GB": r"\b[A-Z9]{5}\d{6}[A-Z9]{2}\d[A-Z]{2}\b",  # 16 char UK DL number (approx structural)
    "VAT_GB": r"\bGB\d{9}\b|\bGB\d{12}\b|\bGBGD\d{3}\b|\bGBHA\d{3}\b",
    "COMPANIES_HOUSE_GB": r"\b(?:SC|NI|OC|SO)?\d{6,8}\b",  # Company number

    # ---------- FRANCE (FR) ----------
    "INSEE_FR": r"\b[12]\d{12,14}\b",  # NIR / INSEE (simplified for RE2 recall; LLM validates)
    "VAT_FR": r"\bFR[A-HJ-NP-Z0-9]{2}\d{9}\b",
    "DRIVERS_LICENSE_FR": r"\b[A-Z0-9]{12}\b",  # French permis (approx)
    "PASSPORT_FR": r"\b\d{2}[A-Z]{2}\d{5}\b",

    # ---------- SPAIN (ES) ----------
    "DNI_ES": r"\b\d{8}[A-HJ-NP-TV-Z]\b",
    "NIE_ES": r"\b[XYZ]\d{7}[A-HJ-NP-TV-Z]\b",
    "CIF_ES": r"\b[A-HJ-NP-S]\d{7}[A-J0-9]\b",  # Company tax ID
    "VAT_ES": r"\bES[A-Z0-9]\d{7}[A-Z0-9]\b",
    "DRIVERS_LICENSE_ES": r"\b[A-Z0-9]{9,10}\b",

    # ---------- ITALY (IT) ----------
    "CODICE_FISCALE_IT": r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b",
    "VAT_IT": r"\bIT\d{11}\b",
    "DRIVERS_LICENSE_IT": r"\b[A-Z0-9]{10}\b",

    # ---------- INDIA (IN) ----------
    "AADHAAR_IN": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
    "PAN_IN": r"\b[A-Z]{5}\d{4}[A-Z]\b",  # Permanent Account Number
    "GSTIN_IN": r"\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z0-9]{2}\b",
    "DRIVERS_LICENSE_IN": r"\b[A-Z]{2}\d{2}\s?\d{11}\b|\b[A-Z]{2}-\d{13}\b",

    # ---------- CHINA (CN) ----------
    "RESIDENT_ID_CN": r"\b\d{17}[\dXx]\b",  # 18-digit Resident Identity Card (last may be X)
    "UNIFIED_SOCIAL_CREDIT_CODE_CN": r"\b[A-Z0-9]{18}\b",  # USCC / 统一社会信用代码
    "PASSPORT_CN": r"\bE\d{8}\b|\bG\d{8}\b|\bS\d{8}\b",  # Common formats

    # ---------- GERMANY (DE) ----------
    "STEUER_ID_DE": r"\b\d{11}\b",  # Personal tax ID (11 digits)
    "VAT_DE": r"\bDE\d{9}\b",
    "PERSONALAUSWEIS_DE": r"\b[A-Z0-9]{9,10}\b",  # approx ID card / passport style
    "DRIVERS_LICENSE_DE": r"\b[A-Z0-9]{11,12}\b",

    # ---------- JAPAN (JP) ----------
    "MY_NUMBER_JP": r"\b\d{4}\s?\d{4}\s?\d{4}\b",  # 12-digit Individual Number
    "RESIDENT_CARD_JP": r"\b[A-Z]{2}\d{8}\b",  # approx
    "DRIVERS_LICENSE_JP": r"\b\d{12}\b",

    # ---------- SOUTH KOREA (KR) ----------
    "RESIDENT_REGISTRATION_KR": r"\b\d{6}-\d{7}\b",  # RRN (with dash)
    "BUSINESS_REG_KR": r"\b\d{3}-\d{2}-\d{5}\b",

    # ---------- AUSTRALIA (AU) / NEW ZEALAND (NZ) ----------
    "TFN_AU": r"\b\d{3}\s?\d{3}\s?\d{3}\b",  # Tax File Number
    "ABN_AU": r"\b\d{2}\s?\d{3}\s?\d{3}\s?\d{3}\b",  # Australian Business Number
    "DRIVERS_LICENSE_AU": r"\b[A-Z0-9]{8,10}\b",
    "IRD_NZ": r"\b\d{2,3}-\d{3,4}-\d{3}\b",  # IRD number (tax)

    # ---------- BRAZIL (BR) ----------
    "CPF_BR": r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",  # Pessoa Física
    "CNPJ_BR": r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b",  # Pessoa Jurídica (business)
    "RG_BR": r"\b\d{2}\.?\d{3}\.?\d{3}-?[0-9X]\b",

    # ---------- MEXICO (MX) / ARGENTINA (AR) ----------
    "CURP_MX": r"\b[A-Z]{4}\d{6}[HM][A-Z]{5}[0-9A-Z]\d\b",
    "RFC_MX": r"\b[A-Z]{3,4}\d{6}[A-Z0-9]{3}\b",
    "DNI_AR": r"\b\d{8}\b",  # Argentine ID (often 8 digits + verification in context)

    # ---------- SOUTH AFRICA (ZA) ----------
    "ID_ZA": r"\b\d{13}\b",  # 13-digit SA ID
    "TAX_ZA": r"\b\d{10}\b",

    # ---------- SINGAPORE (SG) / HONG KONG (HK) / TAIWAN (TW) ----------
    "NRIC_SG": r"\b[SGT]\d{7}[A-Z]\b",  # National Registration Identity Card
    "HKID_HK": r"\b[A-Z]{1,2}\d{6}[0-9A]\b",
    "NATIONAL_ID_TW": r"\b[A-Z]\d{9}\b",

    # ---------- EUROPE (selected other) ----------
    "BSN_NL": r"\b\d{9}\b",  # Burgerservicenummer (NL)
    "VAT_NL": r"\bNL\d{9}B\d{2}\b",
    "NISS_BE": r"\b\d{2}\.\d{2}\.\d{2}-\d{3}\.\d{2}\b|\b\d{11}\b",  # BE social security
    "AHV_CH": r"\b756\.\d{4}\.\d{4}\.\d{2}\b|\b756\d{10}\b",  # Swiss social
    "VAT_CH": r"\bCHE\d{9}(?:MWST|TVA|IVA)?\b",
    "SVNR_AT": r"\b\d{10}\b",  # Austrian social security
    "PERSONAL_ID_SE": r"\b\d{6,8}-\d{4}\b",  # Personnummer (SE)
    "NATIONAL_ID_NO": r"\b\d{11}\b",
    "CPR_DK": r"\b\d{6}-\d{4}\b",
    "HETU_FI": r"\b\d{6}[+\-A]\d{3}[0-9A-Z]\b",
    "PESEL_PL": r"\b\d{11}\b",
    "PPS_IE": r"\b\d{7}[A-W]\b",  # Personal Public Service Number (IE)
    "NIF_PT": r"\b\d{9}\b",
    "AMKA_GR": r"\b\d{11}\b",

    # ---------- MIDDLE EAST / OTHER ----------
    "ID_IL": r"\b\d{9}\b",  # Israeli ID (Teudat Zehut)
    "NATIONAL_ID_TR": r"\b\d{11}\b",  # Turkish TC Kimlik
    "PASSPORT_RU": r"\b\d{2}\s?\d{2}\s?\d{6}\b",
    "NATIONAL_ID_TH": r"\b\d{13}\b",  # Thai ID
    "NRIC_MY": r"\b\d{6}-\d{2}-\d{4}\b",  # Malaysian
    "NIK_ID": r"\b\d{16}\b",  # Indonesian

    # ---------- Legacy / aliases kept for compatibility ----------
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",  # maps to US SSN
}


# Config Profiles
class ConfigProfile(str, Enum):
    BEST_QUALITY = "best-quality"
    BEST_SPEED = "best-speed"
    BEST_COST = "best-cost"


# Centralized profiles dictionary
PROFILE_CONFIGS: Dict[ConfigProfile, Dict[str, Any]] = {
    ConfigProfile.BEST_QUALITY: {
        "model_name": "gemini-2.5-pro",
        "prompt_name": "detailed",
        "chunk_size": 15000,
        "chunk_overlap": 2000,
        "max_retries": 5,
        "base_retry_delay": 2.0,
        "max_retry_delay": 60.0,
    },
    ConfigProfile.BEST_SPEED: {
        "model_name": "gemini-2.5-flash",
        "prompt_name": "simple",
        "chunk_size": 30000,
        "chunk_overlap": 1000,
        "max_retries": 3,
        "base_retry_delay": 1.0,
        "max_retry_delay": 10.0,
    },
    ConfigProfile.BEST_COST: {
        "model_name": "gemini-2.5-flash-lite",
        "prompt_name": "simple",
        "chunk_size": 60000,
        "chunk_overlap": 3000,
        "max_retries": 3,
        "base_retry_delay": 1.0,
        "max_retry_delay": 15.0,
    },
}


class AppConfig(BaseModel):
    model_name: str
    prompt_name: str
    chunk_size: int
    chunk_overlap: int
    max_retries: int
    base_retry_delay: float
    max_retry_delay: float
    enable_cache: bool = True
    cache_dir: str = DEFAULT_CACHE_DIR
    cache_file: str = DEFAULT_CACHE_FILE
    anonymized_dir: str = DEFAULT_ANONYMIZED_DIR
    mappings_dir: str = DEFAULT_MAPPINGS_DIR
    deanonymized_dir: str = DEFAULT_DEANONYMIZED_DIR
    stats_dir: str = DEFAULT_STATS_DIR
    log_file: str = DEFAULT_LOG_FILE
    regex_patterns: Dict[str, str] = Field(
        default_factory=lambda: dict(DEFAULT_REGEX_PATTERNS)
    )


def get_config_for_profile(
    profile: ConfigProfile,
    model_name: Optional[str] = None,
    prompt_name: Optional[str] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> AppConfig:
    """Return an AppConfig populated from one of the built-in profiles.

    Profiles provide convenient quality/speed/cost presets. Any of the
    scalar overrides (model_name, prompt_name, chunk_size, chunk_overlap)
    take precedence over the profile defaults.

    The other fields (retries, delays, cache settings, directories) always
    come from the chosen profile.

    Args:
        profile: One of ConfigProfile.BEST_QUALITY, BEST_SPEED or BEST_COST.
        model_name: Optional override for the model (string or provider/model).
        prompt_name: Optional override ("simple" or "detailed").
        chunk_size: Optional override for characters_to_anonymize / chunk_size.
        chunk_overlap: Optional override for chunk overlap.

    Returns:
        A fully populated AppConfig instance ready to drive anonymize_file
        (or to be passed through configure_cache, etc.).
    """
    profile_defaults = PROFILE_CONFIGS[profile]

    resolved_prompt_name = prompt_name or profile_defaults["prompt_name"]
    if isinstance(resolved_prompt_name, Enum):
        resolved_prompt_name = resolved_prompt_name.value

    return AppConfig(
        model_name=model_name or profile_defaults["model_name"],
        prompt_name=resolved_prompt_name,
        chunk_size=chunk_size
        if chunk_size is not None
        else profile_defaults["chunk_size"],
        chunk_overlap=chunk_overlap
        if chunk_overlap is not None
        else profile_defaults["chunk_overlap"],
        max_retries=profile_defaults["max_retries"],
        base_retry_delay=profile_defaults["base_retry_delay"],
        max_retry_delay=profile_defaults["max_retry_delay"],
    )


# Legacy / Existing Enums for compatibility
T = TypeVar("T", bound=Enum)


class PromptEnum(str, Enum):
    simple = "simple"
    detailed = "detailed"


class ModelProvider(str, Enum):
    GOOGLE = "google"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ModelName(str, Enum):
    google_gemini_2_5_pro = "gemini-2.5-pro"
    google_gemini_2_5_flash = "gemini-2.5-flash"
    google_gemini_2_5_flash_lite = "gemini-2.5-flash-lite"
    ollama_gemma = "gemma:7b"
    ollama_phi = "phi4-mini"
    huggingface_mistral_7b_instruct = "mistralai/Mistral-7B-Instruct-v0.1"
    huggingface_zephyr_7b_beta = "HuggingFaceH4/zephyr-7b-beta"
    huggingface_openai_gpt_oss_20b = "openai/gpt-oss-20b"
    openrouter_gpt_4o = "openai/gpt-4o"
    openrouter_gemini_pro = "google/gemini-pro"
    openai_gpt_4o = "gpt-4o"
    openai_gpt_5 = "gpt-5"
    anthropic_claude_4_sonet = "claude-4-sonet"
    anthropic_claude_4_sonet_4_5 = "claude-4.5-sonet"

    @property
    def provider(self) -> ModelProvider:
        provider_name = self.name.split("_")[0].upper()
        return ModelProvider[provider_name]


def get_enum_value(enum_type: Type[T], value: str) -> T:
    try:
        return enum_type(value)
    except ValueError as e:
        raise ValueError(
            f"Invalid value '{value}' for enum {enum_type.__name__}"
        ) from e


def get_provider_and_model_name(model_name_str: str) -> tuple[str, str]:
    try:
        model_enum = ModelName(model_name_str)
        return model_enum.provider.value, model_enum.value
    except ValueError:
        if "/" not in model_name_str:
            raise ValueError(
                f"'{model_name_str}' is not a known model and is not in the "
                "'provider/model_name' format."
            ) from None

        provider_name, model_identifier = model_name_str.split("/", 1)
        try:
            ModelProvider(provider_name)
            return provider_name, model_identifier
        except ValueError:
            raise ValueError(
                f"Unknown provider '{provider_name}' in custom model string."
            ) from None
