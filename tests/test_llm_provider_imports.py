import unittest
from unittest.mock import patch
import sys
from pdf_anonymizer_core.llm_provider import (
    GoogleProvider,
    OllamaProvider,
    HuggingFaceProvider,
    OpenRouterProvider,
    OpenAIProvider,
    AnthropicProvider,
)

class TestLLMProviderImports(unittest.TestCase):
    def test_google_provider_import_error(self):
        with patch.dict(sys.modules, {'google': None}):
            with self.assertRaisesRegex(ImportError, "The 'google' extra is not installed"):
                GoogleProvider()

    def test_ollama_provider_import_error(self):
        with patch.dict(sys.modules, {'ollama': None}):
            with self.assertRaisesRegex(ImportError, "The 'ollama' extra is not installed"):
                OllamaProvider()

    def test_huggingface_provider_import_error(self):
        with patch.dict(sys.modules, {'huggingface_hub': None}):
            with self.assertRaisesRegex(ImportError, "The 'huggingface' extra is not installed"):
                HuggingFaceProvider()

    def test_openrouter_provider_import_error(self):
        # OpenRouter uses 'openai'
        with patch.dict(sys.modules, {'openai': None}):
            with self.assertRaisesRegex(ImportError, "The 'openrouter' extra is not installed"):
                OpenRouterProvider()

    def test_openai_provider_import_error(self):
        with patch.dict(sys.modules, {'openai': None}):
            with self.assertRaisesRegex(ImportError, "The 'openai' extra is not installed"):
                OpenAIProvider()

    def test_anthropic_provider_import_error(self):
        with patch.dict(sys.modules, {'anthropic': None}):
            with self.assertRaisesRegex(ImportError, "The 'anthropic' extra is not installed"):
                AnthropicProvider()

if __name__ == "__main__":
    unittest.main()
