"""Tests for implied / identity-clue instructions in the detailed prompt.

The detailed prompt must ask the model to hide phrases that point to one
person even when no name is written. The simple prompt must stay unchanged
so the faster / cheaper profiles do not pay for this extra work.
"""

from pdf_anonymizer_core.call_llm import identify_entities_with_llm
from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.prompts import detailed, simple


class TestDetailedPromptAsksForIdentityClues:
    def test_detailed_prompt_defines_indirect_type(self) -> None:
        assert "**INDIRECT:**" in detailed.prompt_template
        assert "does not contain a person's name" in detailed.prompt_template

    def test_detailed_prompt_has_job_company_city_example(self) -> None:
        assert "CEO of Tesla" in detailed.prompt_template
        assert "Austin" in detailed.prompt_template
        assert '"type": "PERSON"' in detailed.prompt_template
        assert "Elon Musk" in detailed.prompt_template

    def test_detailed_prompt_has_author_of_example(self) -> None:
        assert "author of the 'Harry Potter' series" in detailed.prompt_template
        assert "J.K. Rowling" in detailed.prompt_template

    def test_detailed_prompt_has_unique_role_example(self) -> None:
        assert "only in-house patent counsel" in detailed.prompt_template
        assert '"type": "INDIRECT"' in detailed.prompt_template

    def test_detailed_prompt_tells_model_when_not_to_mark_vague_phrases(self) -> None:
        assert "Do NOT mark a vague phrase" in detailed.prompt_template
        assert "the CEO" in detailed.prompt_template

    def test_simple_prompt_does_not_mention_indirect(self) -> None:
        assert "INDIRECT" not in simple.prompt_template
        assert "CEO of Tesla" not in simple.prompt_template
        assert "Harry Potter" not in simple.prompt_template


class TestIndirectEntitiesRoundTrip:
    def test_llm_parser_accepts_indirect_entities(self, mocker) -> None:
        mock_provider = mocker.Mock()
        mock_provider.call.return_value = """
        {
            "entities": [
                {
                    "text": "Acme Inc.'s only in-house patent counsel",
                    "type": "INDIRECT",
                    "base_form": "Acme Inc.'s only in-house patent counsel"
                }
            ]
        }
        """
        mocker.patch(
            "pdf_anonymizer_core.call_llm.get_provider",
            return_value=mock_provider,
        )

        entities = identify_entities_with_llm(
            "Please copy Acme Inc.'s only in-house patent counsel.",
            prompt_template=detailed.prompt_template,
            model_name="gemini-2.5-flash",
        )

        assert entities == [
            {
                "text": "Acme Inc.'s only in-house patent counsel",
                "type": "INDIRECT",
                "base_form": "Acme Inc.'s only in-house patent counsel",
                "score": 0.7,
                "source": "llm",
            }
        ]

    def test_anonymize_replaces_indirect_phrase(self, mocker) -> None:
        mocker.patch("os.path.getsize", return_value=0)
        text = (
            "Please copy Acme Inc.'s only in-house patent counsel. "
            "The meeting is in Springfield."
        )
        mocker.patch(
            "pdf_anonymizer_core.core.load_and_extract_text_from_file",
            return_value=(text, [text]),
        )
        mocker.patch(
            "pdf_anonymizer_core.core.identify_entities_with_llm",
            return_value=[
                {
                    "text": "Acme Inc.'s only in-house patent counsel",
                    "type": "INDIRECT",
                    "base_form": "Acme Inc.'s only in-house patent counsel",
                },
                {
                    "text": "Springfield",
                    "type": "LOCATION",
                    "base_form": "Springfield",
                },
            ],
        )
        mocker.patch(
            "pdf_anonymizer_core.core.extract_entities_via_regex",
            return_value=[],
        )

        anonymized_text, mapping = anonymize_file(
            "dummy.pdf", 1000, detailed.prompt_template, "dummy_model"
        )

        assert "only in-house patent counsel" not in anonymized_text
        assert "INDIRECT_1" in anonymized_text
        assert "LOCATION_1" in anonymized_text
        assert mapping["Acme Inc.'s only in-house patent counsel"] == "INDIRECT_1"
        assert mapping["Springfield"] == "LOCATION_1"

    def test_implied_person_shares_base_form_with_later_name(self, mocker) -> None:
        mocker.patch("os.path.getsize", return_value=0)
        text = "We met the CEO of Tesla. Later Elon Musk joined the call."
        mocker.patch(
            "pdf_anonymizer_core.core.load_and_extract_text_from_file",
            return_value=(text, [text]),
        )
        mocker.patch(
            "pdf_anonymizer_core.core.identify_entities_with_llm",
            return_value=[
                {
                    "text": "CEO of Tesla",
                    "type": "PERSON",
                    "base_form": "Elon Musk",
                },
                {
                    "text": "Tesla",
                    "type": "ORGANIZATION",
                    "base_form": "Tesla",
                },
                {
                    "text": "Elon Musk",
                    "type": "PERSON",
                    "base_form": "Elon Musk",
                },
            ],
        )
        mocker.patch(
            "pdf_anonymizer_core.core.extract_entities_via_regex",
            return_value=[],
        )

        anonymized_text, mapping = anonymize_file(
            "dummy.pdf", 1000, detailed.prompt_template, "dummy_model"
        )

        assert "CEO of Tesla" not in anonymized_text
        assert "Elon Musk" not in anonymized_text
        assert mapping["Elon Musk"] == "PERSON_1"
        assert mapping["CEO of Tesla"] == "PERSON_1.v_1"
        assert "PERSON_1" in anonymized_text
