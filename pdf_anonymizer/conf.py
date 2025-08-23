from enum import Enum

# Default values
DEFAULT_CHARACTERS_TO_ANONYMIZE = 100000
DEFAULT_PROMPT_NAME = "detailed"
DEFAULT_MODEL_NAME = "gemini-2.5-flash-lite"

# Enum for prompt names
class PromptEnum(str, Enum):
    simple = "simple"
    detailed = "detailed"


class ModelName(str, Enum):
    gemini_2_5_pro = "gemini-2.5-pro"
    gemini_2_5_flash = "gemini-2.5-flash"
    gemini_2_5_flash_lite = "gemini-2.5-flash-lite"
    gemma = "gemma"
    phi = "phi4-mini"
