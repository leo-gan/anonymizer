import os
from abc import ABC, abstractmethod
from typing import Any, Dict


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def call(self, prompt: str, model_name: str) -> str:
        """
        Call the language model and return the text content of the response.
        """
        pass


class GoogleProvider(LLMProvider):
    def __init__(self):
        try:
            from google import genai

            self.genai = genai
        except ImportError:
            raise ImportError(
                "The 'google' extra is not installed. "
                "Please run 'pip install \"pdf-anonymizer-core[google]\"'."
            )
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY environment variable not set.")

    def call(self, prompt: str, model_name: str) -> str:
        client = self.genai.Client()
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text if hasattr(response, "text") else ""


class OllamaProvider(LLMProvider):
    def __init__(self):
        try:
            import ollama

            self.ollama = ollama
        except ImportError:
            raise ImportError(
                "The 'ollama' extra is not installed. "
                "Please run 'pip install \"pdf-anonymizer-core[ollama]\"'."
            )

    def call(self, prompt: str, model_name: str) -> str:
        response: Dict[str, Any] = self.ollama.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        if (
            isinstance(response, dict)
            and "message" in response
            and "content" in response["message"]
        ):
            return response["message"]["content"]
        return ""


class HuggingFaceProvider(LLMProvider):
    def __init__(self):
        try:
            from huggingface_hub import InferenceClient

            self.InferenceClient = InferenceClient
        except ImportError:
            raise ImportError(
                "The 'huggingface' extra is not installed. "
                "Please run 'pip install \"pdf-anonymizer-core[huggingface]\"'."
            )
        if not os.getenv("HUGGING_FACE_TOKEN"):
            raise ValueError("HUGGING_FACE_TOKEN environment variable not set.")

    def call(self, prompt: str, model_name: str) -> str:
        client = self.InferenceClient(
            model=model_name, token=os.getenv("HUGGING_FACE_TOKEN")
        )
        response = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
        )
        if (
            response
            and hasattr(response, "choices")
            and response.choices
            and hasattr(response.choices[0], "message")
            and hasattr(response.choices[0].message, "content")
        ):
            return response.choices[0].message.content or ""
        return ""


class OpenRouterProvider(LLMProvider):
    def __init__(self):
        try:
            from openai import OpenAI

            self.OpenAI = OpenAI
        except ImportError:
            raise ImportError(
                "The 'openrouter' extra is not installed. "
                "Please run 'pip install \"pdf-anonymizer-core[openrouter]\"'."
            )
        if not os.getenv("OPENROUTER_API_KEY"):
            raise ValueError("OPENROUTER_API_KEY environment variable not set.")

    def call(self, prompt: str, model_name: str) -> str:
        client = self.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        completion = client.chat.completions.create(
            model=model_name, messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content or ""


class OpenAIProvider(LLMProvider):
    def __init__(self):
        try:
            from openai import OpenAI

            self.OpenAI = OpenAI
        except ImportError:
            raise ImportError(
                "The 'openai' extra is not installed. "
                "Please run 'pip install \"pdf-anonymizer-core[openai]\"'."
            )
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable not set.")

    def call(self, prompt: str, model_name: str) -> str:
        client = self.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        completion = client.chat.completions.create(
            model=model_name, messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content or ""


class AnthropicProvider(LLMProvider):
    def __init__(self):
        try:
            from anthropic import Anthropic

            self.Anthropic = Anthropic
        except ImportError:
            raise ImportError(
                "The 'anthropic' extra is not installed. "
                "Please run 'pip install \"pdf-anonymizer-core[anthropic]\"'."
            )
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY environment variable not set.")

    def call(self, prompt: str, model_name: str) -> str:
        client = self.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text if response.content else ""


def get_provider(provider_name: str) -> LLMProvider:
    """Factory function to get a provider instance."""
    provider_map = {
        "google": GoogleProvider,
        "ollama": OllamaProvider,
        "huggingface": HuggingFaceProvider,
        "openrouter": OpenRouterProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
    }
    provider_class = provider_map.get(provider_name)
    if provider_class:
        return provider_class()
    raise ValueError(f"Unknown provider: {provider_name}")
