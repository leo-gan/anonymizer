"""Independent gold-corpus gate for id-extract (detection only)."""

import json

from id_extract import extract

from tests.eval.gold import (
    CI_GOLD_SOURCES,
    ID_EXTRACT_BASELINE_PATH,
    evaluate_documents,
    load_gold_corpus,
    structured_mentions,
)
from tests.eval.metrics import mention_scores


def _predict(text: str):
    return [
        {
            "text": item["text"],
            "type": item["type"],
            "start": item["start"],
            "end": item["end"],
            "base_form": item.get("base_form") or item["text"],
        }
        for item in extract(text)
    ]


def test_id_extract_structured_recall_on_ci_gold() -> None:
    documents = load_gold_corpus(sources=list(CI_GOLD_SOURCES), include_committed=True)
    assert documents
    gold_structured = []
    predicted = []
    for document in documents:
        gold_structured.extend(structured_mentions(document["mentions"]))
        predicted.extend(_predict(document["text"]))
    scores = mention_scores(gold_structured, predicted)
    assert scores["recall"] == 1.0


def test_id_extract_committed_baseline_exists() -> None:
    report = json.loads(ID_EXTRACT_BASELINE_PATH.read_text(encoding="utf-8"))
    assert report["package"] == "id-extract"
    assert report["profile"] == "extract"
    assert report["countries"] == "all"
    assert report["documents"] > 0
    mention = report["overall"]["scores"]["all"]["mention"]
    assert mention["recall"] >= 0.0


def test_id_extract_ci_gold_meets_committed_baseline() -> None:
    documents = load_gold_corpus(sources=list(CI_GOLD_SOURCES), include_committed=True)
    preds = [_predict(document["text"]) for document in documents]
    live = evaluate_documents(documents, preds)
    baseline = json.loads(ID_EXTRACT_BASELINE_PATH.read_text(encoding="utf-8"))
    live_recall = live["scores"]["all"]["mention"]["recall"]
    base_recall = baseline["overall"]["scores"]["all"]["mention"]["recall"]
    assert live_recall + 1e-9 >= base_recall
    live_struct = mention_scores(
        [m for doc in documents for m in structured_mentions(doc["mentions"])],
        [hit for pred in preds for hit in pred],
    )
    assert (
        live_struct["recall"] >= baseline["overall"]["structured"]["mention"]["recall"]
    )
