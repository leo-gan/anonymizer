"""Contract tests for provider response shapes.

These tests do not call a live model. Each one hands the adapter a stand-in
client with the attributes the real SDK returns, then checks that the adapter
reads the text. The Anthropic stand-in rejects ``stream=True``, because that
call returns a stream manager rather than a completed message.
"""

from pdf_anonymizer_core.llm_provider import (
    AnthropicProvider,
    GoogleProvider,
    HuggingFaceProvider,
    OllamaProvider,
    OpenAIProvider,
    OpenRouterProvider,
)


def test_google_reads_response_text(monkeypatch) -> None:
    monkeypatch.delenv("ANONYMIZER_GEMINI_TEMPERATURE", raising=False)
    monkeypatch.delenv("ANONYMIZER_GEMINI_THINKING_BUDGET", raising=False)

    class Models:
        def generate_content(self, **kwargs):
            return type("Response", (), {"text": "from-google"})()

    class GenAI:
        class Client:
            def __init__(self):
                self.models = Models()

    provider = GoogleProvider.__new__(GoogleProvider)
    provider.genai = GenAI()
    assert provider._call_raw("prompt", "gemini-test") == "from-google"


def test_ollama_reads_message_content() -> None:
    class Ollama:
        @staticmethod
        def chat(**kwargs):
            return {
                "message": {"content": "from-ollama"},
                "prompt_eval_count": 1,
                "eval_count": 2,
            }

    provider = OllamaProvider.__new__(OllamaProvider)
    provider.ollama = Ollama()
    assert provider._call_raw("prompt", "local-test") == "from-ollama"


def test_huggingface_reads_choice_content(monkeypatch) -> None:
    monkeypatch.setenv("HUGGING_FACE_TOKEN", "test-token")

    class Choice:
        message = type("Message", (), {"content": "from-hf"})()

    class Response:
        choices = [Choice()]

    class InferenceClient:
        def __init__(self, model, token):
            assert token == "test-token"

        def chat_completion(self, **kwargs):
            return Response()

    provider = HuggingFaceProvider.__new__(HuggingFaceProvider)
    provider.InferenceClient = InferenceClient
    assert provider._call_raw("prompt", "org/model") == "from-hf"


def _completion(text: str):
    message = type("Message", (), {"content": text})()
    choice = type("Choice", (), {"message": message})()
    return type("Completion", (), {"choices": [choice]})()


def test_openai_reads_choice_content(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class OpenAI:
        def __init__(self, api_key=None, base_url=None):
            self.chat = type(
                "Chat",
                (),
                {"completions": type("C", (), {"create": staticmethod(lambda **k: _completion("from-openai"))})()},
            )()

    provider = OpenAIProvider.__new__(OpenAIProvider)
    provider.OpenAI = OpenAI
    assert provider._call_raw("prompt", "gpt-test") == "from-openai"


def test_openrouter_reads_choice_content(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    class OpenAI:
        def __init__(self, api_key=None, base_url=None):
            assert base_url == "https://openrouter.ai/api/v1"
            self.chat = type(
                "Chat",
                (),
                {
                    "completions": type(
                        "C",
                        (),
                        {"create": staticmethod(lambda **k: _completion("from-router"))},
                    )()
                },
            )()

    provider = OpenRouterProvider.__new__(OpenRouterProvider)
    provider.OpenAI = OpenAI
    assert provider._call_raw("prompt", "vendor/model") == "from-router"


def test_anthropic_reads_a_completed_message(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    seen = {}

    class Messages:
        def create(self, **kwargs):
            seen.update(kwargs)
            if kwargs.get("stream") is True:
                raise AssertionError("stream=True does not return response.content")
            block = type("Block", (), {"text": "from-anthropic"})()
            return type("Message", (), {"content": [block]})()

    class Anthropic:
        def __init__(self, api_key):
            assert api_key == "test-key"
            self.messages = Messages()

    provider = AnthropicProvider.__new__(AnthropicProvider)
    provider.Anthropic = Anthropic
    assert provider._call_raw("prompt", "claude-test") == "from-anthropic"
    assert seen.get("stream") is not True
