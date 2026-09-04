"""TAB-style scores on the mini fixture."""

import json
from pathlib import Path

from pdf_anonymizer_core.regex_ner import extract_entities_via_regex
from pdf_anonymizer_core.conf import DEFAULT_REGEX_PATTERNS

from tests.eval.metrics import entity_recall, evaluate_fixture, mention_scores

FIXTURE_PATH = Path(__file__).with_name("fixture.json")


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_perfect_predictions_score_one() -> None:
    fixture = _load_fixture()
    gold = fixture["mentions"]
    mention = mention_scores(gold, gold)
    entity = entity_recall(gold, gold)
    assert mention["recall"] == 1.0
    assert mention["precision"] == 1.0
    assert entity["recall"] == 1.0


def test_missing_direct_id_lowers_direct_recall() -> None:
    fixture = _load_fixture()
    gold = fixture["mentions"]
    predicted = [m for m in gold if m["type"] != "EMAIL"]
    report = evaluate_fixture(fixture, predicted)
    assert report["scores"]["direct"]["mention"]["recall"] < 1.0
    assert report["scores"]["quasi"]["mention"]["recall"] == 1.0


def test_regex_stage_on_fixture_finds_structured_direct() -> None:
    fixture = _load_fixture()
    ents = extract_entities_via_regex(fixture["text"], DEFAULT_REGEX_PATTERNS)
    predicted = [
        {
            "text": e["text"],
            "type": e["type"],
            "start": e.get("start"),
            "end": e.get("end"),
        }
        for e in ents
    ]
    report = evaluate_fixture(fixture, predicted)
    # Regex should catch email (and likely the ISO date). Names need the LLM.
    assert report["scores"]["direct"]["mention"]["recall"] > 0
    email_gold = [m for m in fixture["mentions"] if m["type"] == "EMAIL"]
    email_pred = [p for p in predicted if p["type"] == "EMAIL"]
    assert mention_scores(email_gold, email_pred)["recall"] == 1.0
