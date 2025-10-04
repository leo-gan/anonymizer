from enum import Enum
from typing import Type, TypeVar

# Default values
DEFAULT_CHARACTERS_TO_ANONYMIZE: int = 100000
DEFAULT_PROMPT_NAME: str = "detailed"
DEFAULT_MODEL_NAME: str = "gemini-2.5-flash"

# Type variable for enum values
T = TypeVar("T", bound=Enum)


# Enum for prompt names
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


# Then you could associate a provider with each model, for instance:
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
    def provider(self) -> "ModelProvider":
        provider_name = self.name.split("_")[0].upper()
        return ModelProvider[provider_name]


def get_enum_value(enum_type: Type[T], value: str) -> T:
    """Safely get an enum value from a string.

    Args:
        enum_type: The enum class to get the value from.
        value: The string value to look up in the enum.

    Returns:
        The corresponding enum member.

    Raises:
        ValueError: If the value is not found in the enum.
    """
    try:
        return enum_type(value)
    except ValueError as e:
        raise ValueError(
            f"Invalid value '{value}' for enum {enum_type.__name__}"
        ) from e


def get_provider_and_model_name(model_name_str: str) -> tuple[str, str]:
    """
    Resolves the provider and model name from a string.
    The string can be either a value from the ModelName enum or a custom string
    in the format "provider/model-identifier".
    Args:
        model_name_str: The model name string to resolve.
    Returns:
        A tuple containing the provider name and the actual model name.
    Raises:
        ValueError: If the model name is invalid or the provider is unknown.
    """
    try:
        # Try to find the model in the ModelName enum
        model_enum = ModelName(model_name_str)
        return model_enum.provider.value, model_enum.value
    except ValueError:
        # If not in enum, treat as a "provider/model_name" string
        if "/" not in model_name_str:
            raise ValueError(
                f"'{model_name_str}' is not a known model and is not in the "
                "'provider/model_name' format."
            ) from None

        provider_name, model_identifier = model_name_str.split("/", 1)
        try:
            # Check if the extracted provider is valid
            ModelProvider(provider_name)
            return provider_name, model_identifier
        except ValueError:
            raise ValueError(
                f"Unknown provider '{provider_name}' in custom model string."
            ) from None
