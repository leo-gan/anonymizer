import os
import json
import hashlib
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from threading import Lock

from pdf_anonymizer_core.conf import DEFAULT_CHARACTERS_TO_ANONYMIZE

# Thread-safe Local LLM Response Cache
class LocalLLMCache:
    def __init__(self, cache_dir: str = "data/cache", cache_file: str = "llm_responses.json"):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, cache_file)
        self.lock = Lock()
        self._cache = {}
        self._load_cache()

    def _load_cache(self):
        with self.lock:
            if os.path.exists(self.cache_file):
                try:
                    with open(self.cache_file, "r", encoding="utf-8") as f:
                        self._cache = json.load(f)
                except Exception as e:
                    logging.warning(f"Failed to load LLM cache file: {e}")
                    self._cache = {}

    def _save_cache(self):
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            with self.lock:
                with open(self.cache_file, "w", encoding="utf-8") as f:
                    json.dump(self._cache, f, indent=4)
        except Exception as e:
            logging.warning(f"Failed to save LLM cache file: {e}")

    def get(self, model_name: str, prompt: str) -> Optional[str]:
        prompt_hash = hashlib.md5(prompt.encode("utf-8")).hexdigest()
        key = f"{model_name}:{prompt_hash}"
        with self.lock:
            return self._cache.get(key)

    def set(self, model_name: str, prompt: str, response: str):
        prompt_hash = hashlib.md5(prompt.encode("utf-8")).hexdigest()
        key = f"{model_name}:{prompt_hash}"
        with self.lock:
            self._cache[key] = response
        self._save_cache()

_cache_instance: Optional[LocalLLMCache] = None
_cache_enabled: bool = True

def configure_cache(enabled: bool, cache_dir: str = "data/cache", cache_file: str = "llm_responses.json"):
    global _cache_instance, _cache_enabled
    _cache_enabled = enabled
    if enabled:
        _cache_instance = LocalLLMCache(cache_dir, cache_file)
    else:
        _cache_instance = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def _call_raw(
        self, prompt: str, model_name: str, max_output_tokens: Optional[int] = None
    ) -> str:
        """Call the language model and return the text content of the response."""
        pass

    def call(
        self, prompt: str, model_name: str, max_output_tokens: Optional[int] = None
    ) -> str:
        """Call the language model, checking the local cache first."""
        global _cache_instance, _cache_enabled
        
        # Initialize default cache if enabled and not yet initialized
        if _cache_enabled and _cache_instance is None:
            from pdf_anonymizer_core.conf import DEFAULT_CACHE_DIR, DEFAULT_CACHE_FILE
            configure_cache(True, DEFAULT_CACHE_DIR, DEFAULT_CACHE_FILE)
            
        if _cache_enabled and _cache_instance is not None:
            cached_val = _cache_instance.get(model_name, prompt)
            if cached_val is not None:
                logging.info(f"Cache hit for model '{model_name}'")
                return cached_val
                
        response = self._call_raw(prompt, model_name, max_output_tokens)
        
        if _cache_enabled and _cache_instance is not None and response:
            _cache_instance.set(model_name, prompt, response)
            
        return response


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

    def _call_raw(
        self, prompt: str, model_name: str, max_output_tokens: Optional[int] = None
    ) -> str:
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

    def _call_raw(
        self, prompt: str, model_name: str, max_output_tokens: Optional[int] = None
    ) -> str:
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

    def _call_raw(
        self, prompt: str, model_name: str, max_output_tokens: Optional[int] = None
    ) -> str:
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

    def _call_raw(
        self, prompt: str, model_name: str, max_output_tokens: Optional[int] = None
    ) -> str:
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

    def _call_raw(
        self, prompt: str, model_name: str, max_output_tokens: Optional[int] = None
    ) -> str:
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

    def _call_raw(
        self, prompt: str, model_name: str, max_output_tokens: Optional[int] = None
    ) -> str:
        client = self.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=model_name,
            max_tokens=max_output_tokens
            if isinstance(max_output_tokens, int) and max_output_tokens > 0
            else DEFAULT_CHARACTERS_TO_ANONYMIZE // 4,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
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
