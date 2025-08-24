from enum import Enum

# Default values
DEFAULT_CHARACTERS_TO_ANONYMIZE = 100000
DEFAULT_PROMPT_NAME = "detailed"
DEFAULT_MODEL_NAME = "gemini-2.5-flash-lite"

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
    gemma = "gemma:7b"
    phi = "phi4-mini"

    @property
    def provider(self) -> ModelProvider:
        if "gemini" in self.value:
            return ModelProvider.GOOGLE
        return ModelProvider.OLLAMA