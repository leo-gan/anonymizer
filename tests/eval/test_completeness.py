"""CI gold-corpus system test and leftover red-team gate."""

from pathlib import Path

from pdf_anonymizer_core.conf import DEFAULT_REGEX_PATTERNS
from pdf_anonymizer_core.core import anonymize_text_content
from pdf_anonymizer_core.regex_ner import extract_entities_via_regex
from pdf_anonymizer_core.verify import verify_anonymized_text, write_residual_report

from tests.eval.gold import (
    CI_GOLD_SOURCES,
    DEFAULT_DEST,
    DOWNLOADED_STRUCTURED_LEFTOVER_CEILING,
    STRUCTURED_LEFTOVER_CEILING,
    leftover_report,
    load_gold_corpus,
    structured_mentions,
    structured_residual_hits,
)
from tests.eval.metrics import mention_scores


def _anonymize(text: str) -> str:
    anonymized, _mapping = anonymize_text_content(
        text,
        [text],
        prompt_template="",
        model_name="",
        use_llm=False,
    )
    return anonymized


def test_ci_gold_structured_recall_and_leftover_ceiling() -> None:
    documents = load_gold_corpus(sources=list(CI_GOLD_SOURCES), include_committed=True)
    assert documents
    gold_structured = []
    predicted = []
    leftovers = []
    for document in documents:
        anonymized = _anonymize(document["text"])
        leftovers.append(leftover_report(document["mentions"], anonymized))
        gold_structured.extend(
            {"text": mention["text"], "type": mention["type"]}
            for mention in structured_mentions(document["mentions"])
        )
        predicted.extend(
            {"text": entity["text"], "type": entity["type"]}
            for entity in extract_entities_via_regex(
                document["text"], DEFAULT_REGEX_PATTERNS
            )
        )
    scores = mention_scores(gold_structured, predicted)
    assert scores["recall"] == 1.0
    structured_left = sum(item["structured_leftover"] for item in leftovers)
    structured_gold = sum(item["structured_gold"] for item in leftovers)
    rate = (structured_left / structured_gold) if structured_gold else 0.0
    assert rate <= STRUCTURED_LEFTOVER_CEILING


def test_leftover_red_team_fails_on_residual_pii_json(tmp_path, monkeypatch) -> None:
    documents = load_gold_corpus(sources=list(CI_GOLD_SOURCES), include_committed=True)
    monkeypatch.chdir(tmp_path)
    hits = []
    for index, document in enumerate(documents):
        anonymized = _anonymize(document["text"])
        report = verify_anonymized_text(
            anonymized, anonymized_file=f"{document['name']}.anonymized.md"
        )
        path = write_residual_report(
            report, f"data/anonymized/{document['name']}.anonymized.md"
        )
        assert Path(path).is_file()
        assert Path(path).name.endswith(".residual_pii.json")
        hits.extend(structured_residual_hits(report["regex_hits"]))
    assert hits == []


def test_red_team_gate_detects_leftover_email() -> None:
    report = verify_anonymized_text("Write leftover@example.com and PERSON_1")
    hits = structured_residual_hits(report["regex_hits"])
    assert any(hit["text"] == "leftover@example.com" for hit in hits)


def test_downloaded_corpus_structured_leftover_ceiling() -> None:
    if not (DEFAULT_DEST / "normalized").is_dir():
        return
    documents = load_gold_corpus(include_committed=False, max_docs=200)
    if not documents:
        return
    structured_left = 0
    structured_gold = 0
    for document in documents:
        leftover = leftover_report(document["mentions"], _anonymize(document["text"]))
        structured_left += leftover["structured_leftover"]
        structured_gold += leftover["structured_gold"]
    rate = (structured_left / structured_gold) if structured_gold else 0.0
    assert rate <= DOWNLOADED_STRUCTURED_LEFTOVER_CEILING
