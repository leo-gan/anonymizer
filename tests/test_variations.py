from pytest_mock import MockerFixture

from pdf_anonymizer.core import anonymize_file


def test_consolidate_variations(mocker: MockerFixture) -> None:
    """Variations of an entity are consolidated under a single base placeholder."""
    # Patch where the functions are looked up (in pdf_anonymizer.core)
    mocker.patch("os.path.getsize", return_value=0)
    mocker.patch(
        "pdf_anonymizer.core.load_and_extract_text_from_file",
        return_value=[
            "Mr. John Doe is a consultant. We have a meeting with John Doe tomorrow. Also, we need to review John's latest report."
        ],
    )
    mocker.patch(
        "pdf_anonymizer.core.identify_entities_with_llm",
        return_value=[
            {"text": "Mr. John Doe", "type": "PERSON", "base_form": "John Doe"},
            {"text": "John Doe", "type": "PERSON", "base_form": "John Doe"},
            {"text": "John's", "type": "PERSON", "base_form": "John"},
        ],
    )

    expected_text = (
        "PERSON_1.v_1 is a consultant. We have a meeting with PERSON_1 tomorrow. "
        "Also, we need to review PERSON_1.v_2 latest report."
    )
    expected_mapping = {
        "John Doe": "PERSON_1",
        "Mr. John Doe": "PERSON_1.v_1",
        "John's": "PERSON_1.v_2",
    }

    anonymized_text, final_mapping = anonymize_file(
        "dummy.pdf", 1000, "dummy_prompt", "dummy_model"
    )

    assert anonymized_text.strip() == expected_text
    assert final_mapping == expected_mapping


def test_no_variations(mocker: MockerFixture) -> None:
    """No variations: each entity gets its own base placeholder."""
    mocker.patch("os.path.getsize", return_value=0)
    mocker.patch(
        "pdf_anonymizer.core.load_and_extract_text_from_file",
        return_value=["John Doe met Jane Smith."],
    )
    mocker.patch(
        "pdf_anonymizer.core.identify_entities_with_llm",
        return_value=[
            {"text": "John Doe", "type": "PERSON", "base_form": "John Doe"},
            {"text": "Jane Smith", "type": "PERSON", "base_form": "Jane Smith"},
        ],
    )

    expected_text = "PERSON_1 met PERSON_2."
    expected_mapping = {"John Doe": "PERSON_1", "Jane Smith": "PERSON_2"}

    anonymized_text, final_mapping = anonymize_file(
        "dummy.pdf", 1000, "dummy_prompt", "dummy_model"
    )

    assert anonymized_text.strip() == expected_text
    assert final_mapping == expected_mapping
