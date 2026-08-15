from pdf_anonymizer_core.core import anonymize_file
from pytest_mock import MockerFixture


def test_consolidate_variations(mocker: MockerFixture) -> None:
    """Variations of an entity are consolidated under a single base placeholder."""
    # Patch where the functions are looked up (in pdf_anonymizer_core.core)
    mocker.patch("os.path.getsize", return_value=0)
    text = "Mr. John Doe is a consultant. We have a meeting with John Doe tomorrow. Also, we need to review John's latest report."
    mocker.patch(
        "pdf_anonymizer_core.core.load_and_extract_text_from_file",
        return_value=(text, [text]),
    )
    mocker.patch(
        "pdf_anonymizer_core.core.identify_entities_with_llm",
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
    text = "John Doe met Jane Smith."
    mocker.patch(
        "pdf_anonymizer_core.core.load_and_extract_text_from_file",
        return_value=(text, [text]),
    )
    mocker.patch(
        "pdf_anonymizer_core.core.identify_entities_with_llm",
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


def test_checksum_failure_still_replaced_as_like(mocker: MockerFixture) -> None:
    """A mistyped IBAN is hidden as IBAN_LIKE_1, not left in the clear."""
    mocker.patch("os.path.getsize", return_value=0)
    text = "Pay to GB00WEST12345698765432 today."
    mocker.patch(
        "pdf_anonymizer_core.core.load_and_extract_text_from_file",
        return_value=(text, [text]),
    )
    mocker.patch("pdf_anonymizer_core.core.identify_entities_with_llm", return_value=[])
    mocker.patch(
        "pdf_anonymizer_core.core.extract_entities_via_regex",
        return_value=[
            {
                "text": "GB00WEST12345698765432",
                "type": "IBAN_LIKE",
                "base_form": "GB00WEST12345698765432",
            }
        ],
    )

    anonymized_text, final_mapping = anonymize_file(
        "dummy.pdf", 1000, "dummy_prompt", "dummy_model"
    )

    assert "GB00WEST12345698765432" not in anonymized_text
    assert "IBAN_LIKE_1" in anonymized_text
    assert final_mapping["GB00WEST12345698765432"] == "IBAN_LIKE_1"


def test_iban_filter_includes_like_sibling(mocker: MockerFixture) -> None:
    """Listing IBAN also hides IBAN_LIKE."""
    mocker.patch("os.path.getsize", return_value=0)
    text = "Pay DE89370400440532013000 or GB00WEST12345698765432."
    mocker.patch(
        "pdf_anonymizer_core.core.load_and_extract_text_from_file",
        return_value=(text, [text]),
    )
    mocker.patch("pdf_anonymizer_core.core.identify_entities_with_llm", return_value=[])
    mocker.patch(
        "pdf_anonymizer_core.core.extract_entities_via_regex",
        return_value=[
            {
                "text": "DE89370400440532013000",
                "type": "IBAN",
                "base_form": "DE89370400440532013000",
            },
            {
                "text": "GB00WEST12345698765432",
                "type": "IBAN_LIKE",
                "base_form": "GB00WEST12345698765432",
            },
        ],
    )

    anonymized_text, _final_mapping = anonymize_file(
        "dummy.pdf",
        1000,
        "dummy_prompt",
        "dummy_model",
        anonymized_entities=["IBAN"],
    )

    assert "DE89370400440532013000" not in anonymized_text
    assert "GB00WEST12345698765432" not in anonymized_text
    assert "IBAN_1" in anonymized_text
    assert "IBAN_LIKE_1" in anonymized_text


def test_verified_type_wins_over_like(mocker: MockerFixture) -> None:
    """The same span labeled IBAN and IBAN_LIKE keeps the verified type."""
    mocker.patch("os.path.getsize", return_value=0)
    text = "IBAN DE89370400440532013000"
    mocker.patch(
        "pdf_anonymizer_core.core.load_and_extract_text_from_file",
        return_value=(text, [text]),
    )
    mocker.patch(
        "pdf_anonymizer_core.core.identify_entities_with_llm",
        return_value=[
            {
                "text": "DE89370400440532013000",
                "type": "IBAN_LIKE",
                "base_form": "DE89370400440532013000",
            }
        ],
    )
    mocker.patch(
        "pdf_anonymizer_core.core.extract_entities_via_regex",
        return_value=[
            {
                "text": "DE89370400440532013000",
                "type": "IBAN",
                "base_form": "DE89370400440532013000",
            }
        ],
    )

    anonymized_text, final_mapping = anonymize_file(
        "dummy.pdf", 1000, "dummy_prompt", "dummy_model"
    )

    assert "IBAN_1" in anonymized_text
    assert "IBAN_LIKE" not in anonymized_text
    assert final_mapping["DE89370400440532013000"] == "IBAN_1"
