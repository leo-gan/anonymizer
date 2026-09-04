"""HTTP service (item 22)."""

from __future__ import annotations

import pytest

try:
    from pdf_anonymizer_api.app import (
        MAX_TEXT_CHARS,
        anonymize_text_request,
        create_app,
        deanonymize_text_request,
    )

    _API_IMPORT_ERROR = ""
except ImportError as exc:
    MAX_TEXT_CHARS = 0
    anonymize_text_request = None  # type: ignore[assignment]
    create_app = None  # type: ignore[assignment]
    deanonymize_text_request = None  # type: ignore[assignment]
    _API_IMPORT_ERROR = str(exc)

GOOD_IBAN = "DE89370400440532013000"
BAD_IBAN = "GB00WEST12345698765432"


pytestmark = pytest.mark.skipif(
    anonymize_text_request is None,
    reason=f"pdf-anonymizer-api not installed ({_API_IMPORT_ERROR})",
)


class TestAnonymizeTextRequest:
    def test_regex_only_masks_iban_and_returns_source(self) -> None:
        result = anonymize_text_request(
            f"Pay {GOOD_IBAN} or {BAD_IBAN}.",
            use_llm=False,
        )
        assert GOOD_IBAN not in result["anonymized_text"]
        assert BAD_IBAN not in result["anonymized_text"]
        assert result["mapping"][GOOD_IBAN] == "IBAN_1"
        assert result["mapping"][BAD_IBAN] == "IBAN_LIKE_1"
        by_text = {item["text"]: item for item in result["entities"]}
        assert by_text[GOOD_IBAN]["source"] == "regex"
        assert by_text[GOOD_IBAN]["score"] > by_text[BAD_IBAN]["score"]

    def test_min_confidence_drops_like(self) -> None:
        result = anonymize_text_request(
            f"Pay {GOOD_IBAN} or {BAD_IBAN}.",
            use_llm=False,
            min_confidence=0.8,
        )
        assert GOOD_IBAN not in result["anonymized_text"]
        assert BAD_IBAN in result["anonymized_text"]

    def test_rejects_unknown_prompt(self) -> None:
        with pytest.raises(ValueError, match="prompt_name"):
            anonymize_text_request("hello", prompt_name="nope")

    def test_rejects_oversize_text(self) -> None:
        with pytest.raises(ValueError, match="HTTP limit"):
            anonymize_text_request("x" * (MAX_TEXT_CHARS + 1))


class TestDeanonymizeTextRequest:
    def test_round_trip(self) -> None:
        first = anonymize_text_request("mail ada@example.com", use_llm=False)
        back = deanonymize_text_request(first["anonymized_text"], first["mapping"])
        assert "ada@example.com" in back["text"]
        assert back["restored_count"] >= 1


class TestFastApiRoutes:
    def test_health(self) -> None:
        from fastapi.testclient import TestClient

        client = TestClient(create_app())
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_anonymize_and_deanonymize(self) -> None:
        from fastapi.testclient import TestClient

        client = TestClient(create_app())
        masked = client.post(
            "/anonymize",
            json={"text": "Write to ada@example.com", "use_llm": False},
        )
        assert masked.status_code == 200
        body = masked.json()
        assert "ada@example.com" not in body["anonymized_text"]
        assert body["entities"][0]["source"] == "regex"

        restored = client.post(
            "/deanonymize",
            json={
                "text": body["anonymized_text"],
                "mapping": body["mapping"],
            },
        )
        assert restored.status_code == 200
        assert "ada@example.com" in restored.json()["text"]

    def test_verify_finds_leftover_email(self) -> None:
        from fastapi.testclient import TestClient

        client = TestClient(create_app())
        response = client.post(
            "/verify",
            json={"text": "still visible: ada@example.com"},
        )
        assert response.status_code == 200
        report = response.json()
        assert report["residual_count"] >= 1
        assert report["rewritten"] is False

    def test_report_scores_masked_text(self) -> None:
        from fastapi.testclient import TestClient

        client = TestClient(create_app())
        response = client.post(
            "/report",
            json={"text": "PERSON_1 met ORGANIZATION_1 in LOCATION_1."},
        )
        assert response.status_code == 200
        assert "overall" in response.json()

    def test_bad_prompt_is_400(self) -> None:
        from fastapi.testclient import TestClient

        client = TestClient(create_app())
        response = client.post(
            "/anonymize",
            json={"text": "hello", "prompt_name": "nope"},
        )
        assert response.status_code == 400


class TestCoreStaysFreeOfHttp:
    def test_core_has_no_http_api_module(self) -> None:
        import pdf_anonymizer_core

        assert not hasattr(pdf_anonymizer_core, "http_api")
        import importlib.util

        spec = importlib.util.find_spec("pdf_anonymizer_core.http_api")
        assert spec is None
