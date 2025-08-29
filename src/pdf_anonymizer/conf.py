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


# Then you could associate a provider with each model, for instance:
class ModelName(str, Enum):
    gemini_2_5_pro = "gemini-2.5-pro"
    gemini_2_5_flash = "gemini-2.5-flash"
    gemini_2_5_flash_lite = "gemini-2.5-flash-lite"
    gemma_7b = "gemma:7b"
    phi4_mini = "phi4-mini"

    @property
    def provider(self) -> "ModelProvider":
        if "gemini" in self.value:
            return ModelProvider.GOOGLE
        elif self.value in [self.gemma_7b.value, self.phi4_mini.value]:
            return ModelProvider.OLLAMA
        else:
            raise ValueError(f"Unknown provider for model {self.value}")


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
