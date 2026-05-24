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

# Default Regex Patterns for first-stage NER
DEFAULT_REGEX_PATTERNS: Dict[str, str] = {
    "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "PHONE": r"\+?\b(?:\d{1,4}[- \s]?)?\(?\d{3,4}\)?[- \s]?\d{3,4}(?:[- \s]?\d{3,9})?\b",
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "CREDIT_CARD": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    "IP_ADDRESS": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
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
    regex_patterns: Dict[str, str] = Field(default_factory=lambda: dict(DEFAULT_REGEX_PATTERNS))

def get_config_for_profile(
    profile: ConfigProfile,
    model_name: Optional[str] = None,
    prompt_name: Optional[str] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> AppConfig:
    """Gets the AppConfig instance based on a ConfigProfile with optional overrides."""
    profile_defaults = PROFILE_CONFIGS[profile]
    
    resolved_prompt_name = prompt_name or profile_defaults["prompt_name"]
    if isinstance(resolved_prompt_name, Enum):
        resolved_prompt_name = resolved_prompt_name.value

    return AppConfig(
        model_name=model_name or profile_defaults["model_name"],
        prompt_name=resolved_prompt_name,
        chunk_size=chunk_size if chunk_size is not None else profile_defaults["chunk_size"],
        chunk_overlap=chunk_overlap if chunk_overlap is not None else profile_defaults["chunk_overlap"],
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
