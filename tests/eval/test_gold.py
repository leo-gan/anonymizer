"""Gold-corpus converters, use-case pack, and leftover scoring."""

from pdf_anonymizer_core.conf import DEFAULT_REGEX_PATTERNS
from pdf_anonymizer_core.core import anonymize_text_content
from pdf_anonymizer_core.regex_ner import extract_entities_via_regex

from tests.eval.gold import (
    BASELINE_PATH,
    DEFAULT_DEST,
    is_red_team_type,
    convert_gretel_document,
    convert_presidio_document,
    convert_tab_document,
    leftover_report,
    load_domain_pack,
    load_gold_corpus,
    load_sources_catalog,
    map_entity_type,
)
from tests.eval.metrics import evaluate_fixture

EXPECTED_DOMAINS = {
    "healthcare",
    "legal",
    "government",
    "research",
    "finance",
    "enterprise",
}


def test_sources_catalog_lists_public_tests() -> None:
    catalog = load_sources_catalog()
    ids = {item["id"] for item in catalog["sources"]}
    assert {"tab", "presidio", "gretel", "i2b2-n2c2"}.issubset(ids)
    downloadable = {item["id"] for item in catalog["sources"] if item["downloadable"]}
    assert downloadable == {"tab", "presidio", "gretel"}


def test_red_team_types_are_structured_identifiers() -> None:
    assert is_red_team_type("EMAIL")
    assert is_red_team_type("IBAN_LIKE")
    assert is_red_team_type("CREDIT_CARD")
    assert not is_red_team_type("PERSON")
    assert not is_red_team_type("DATE_ISO")


def test_type_map_covers_public_label_sets() -> None:
    assert map_entity_type("PERSON") == ("PERSON", "direct")
    assert map_entity_type("EMAIL_ADDRESS")[0] == "EMAIL"
    assert map_entity_type("ssn")[0] == "SSN"
    assert map_entity_type("medical_record_number")[0] == "MEDICAL_RECORD"


def test_convert_tab_unions_mask_needed_mentions() -> None:
    raw = {
        "doc_id": "001",
        "dataset_type": "test",
        "text": "Ada from Paris met Bob.",
        "annotations": {
            "ann-a": {
                "entity_mentions": [
                    {
                        "entity_id": "p1",
                        "entity_type": "PERSON",
                        "identifier_type": "DIRECT",
                        "start_offset": 0,
                        "end_offset": 3,
                        "span_text": "Ada",
                    },
                    {
                        "entity_id": "loc1",
                        "entity_type": "LOC",
                        "identifier_type": "NO_MASK",
                        "start_offset": 9,
                        "end_offset": 14,
                        "span_text": "Paris",
                    },
                ]
            },
            "ann-b": {
                "entity_mentions": [
                    {
                        "entity_id": "p1b",
                        "entity_type": "PERSON",
                        "identifier_type": "DIRECT",
                        "start_offset": 0,
                        "end_offset": 3,
                        "span_text": "Ada",
                    },
                    {
                        "entity_id": "p2",
                        "entity_type": "PERSON",
                        "identifier_type": "QUASI",
                        "start_offset": 20,
                        "end_offset": 23,
                        "span_text": "Bob",
                    },
                ]
            },
        },
    }
    doc = convert_tab_document(raw)
    texts = {mention["text"] for mention in doc["mentions"]}
    assert texts == {"Ada", "Bob"}
    assert "Paris" not in texts
    assert doc["domain"] == "legal"


def test_convert_presidio_and_gretel() -> None:
    presidio = convert_presidio_document(
        {
            "full_text": "Write to ada@example.com",
            "spans": [
                {
                    "entity_type": "EMAIL_ADDRESS",
                    "entity_value": "ada@example.com",
                    "start_position": 9,
                    "end_position": 24,
                }
            ],
        },
        0,
    )
    assert presidio["mentions"][0]["type"] == "EMAIL"
    listed = convert_gretel_document(
        {
            "uid": "listed",
            "domain": "healthcare",
            "text": "SSN 123-45-6789",
            "entities": [{"entity": "123-45-6789", "types": ["ssn"]}],
        }
    )
    assert listed["mentions"][0]["type"] == "SSN"
    gretel = convert_gretel_document(
        {
            "uid": "abc",
            "domain": "healthcare",
            "text": "Patient Jordan Hale, SSN 123-45-6789.",
            "entities": "[{'entity': 'Jordan Hale', 'types': ['name']}, "
            "{'entity': '123-45-6789', 'types': ['ssn']}]",
        }
    )
    assert gretel["domain"] == "healthcare"
    types = {mention["type"] for mention in gretel["mentions"]}
    assert types == {"PERSON", "SSN"}


def test_domain_pack_covers_use_cases() -> None:
    docs = load_domain_pack()
    assert {doc["domain"] for doc in docs} == EXPECTED_DOMAINS
    for doc in docs:
        assert doc["text"]
        assert doc["mentions"]
        for mention in doc["mentions"]:
            start, end = mention["start"], mention["end"]
            assert doc["text"][start:end] == mention["text"]


def test_regex_only_hides_structured_domain_pack_pii() -> None:
    docs = load_domain_pack()
    for doc in docs:
        anonymized, _mapping = anonymize_text_content(
            doc["text"],
            [doc["text"]],
            prompt_template="",
            model_name="",
            use_llm=False,
        )
        leftover = leftover_report(doc["mentions"], anonymized)
        assert leftover["structured_leftover"] == 0
        names = [m["text"] for m in doc["mentions"] if m["type"] == "PERSON"]
        for name in names:
            assert name in anonymized


def test_regex_stage_scores_mini_tab_email() -> None:
    corpus = load_gold_corpus(sources=["mini-tab"], include_committed=True)
    assert len(corpus) == 1
    ents = extract_entities_via_regex(corpus[0]["text"], DEFAULT_REGEX_PATTERNS)
    predicted = [
        {
            "text": e["text"],
            "type": e["type"],
            "start": e.get("start"),
            "end": e.get("end"),
        }
        for e in ents
    ]
    report = evaluate_fixture(corpus[0], predicted)
    email_gold = [m for m in corpus[0]["mentions"] if m["type"] == "EMAIL"]
    assert email_gold
    assert report["scores"]["direct"]["mention"]["recall"] > 0


def test_public_eval_table_has_regex_row() -> None:
    table = (BASELINE_PATH.parent / "public_eval_table.md").read_text(encoding="utf-8")
    assert "| regex-only |" in table
    assert "not shipped (item 20)" in table


def test_committed_regex_baseline_covers_use_cases() -> None:
    import json

    report = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    assert report["profile"] == "regex-only"
    assert report["documents"] > 0
    assert {"tab", "presidio", "gretel", "domain-pack"}.issubset(set(report["sources"]))
    assert EXPECTED_DOMAINS.issubset(set(report["domains"]))
    leftover = report["overall"]["leftover"]
    assert leftover["structured_leftover_rate"] < leftover["leftover_rate"]


def test_downloaded_corpus_optional_smoke() -> None:
    if not (DEFAULT_DEST / "normalized").is_dir():
        return
    docs = load_gold_corpus(max_docs=3, include_committed=False)
    if not docs:
        return
    for doc in docs:
        assert doc["text"]
        assert doc["source"] in {"tab", "presidio", "gretel"}
