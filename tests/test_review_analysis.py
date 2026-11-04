"""
PyTest suite for Phase 8 — real-data sentiment baseline, authenticity NOT_VALIDATED, dataset integrity.
"""

import json
import pandas as pd
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.services.review_analysis_service import (
    analyze_product_reviews,
    classify_review_sentiment,
)
from app.services.sentiment_service import analyze_sentiment, get_model_info, MODEL_DIR

client = TestClient(app)
ROOT = Path(__file__).resolve().parent.parent
DS = ROOT / "data" / "review_dataset"


def test_model_artifacts_and_metadata():
    for name in ["tfidf_vectorizer.joblib", "sentiment_logistic_regression.joblib",
                 "model_metadata.json", "evaluation_report.json"]:
        assert (MODEL_DIR / name).exists(), name
    meta = json.loads((MODEL_DIR / "model_metadata.json").read_text(encoding="utf-8"))
    assert meta["train_rows"] == 80000 and meta["test_rows"] == 20000
    assert meta["label_type"] == "RATING_DERIVED"
    assert get_model_info()["is_fake_review_detector"] is False


def test_dataset_counts_and_no_leakage():
    train = pd.read_csv(DS / "train" / "beauty_reviews_train_80k.csv")
    test = pd.read_csv(DS / "test" / "beauty_reviews_test_20k.csv")
    sel = pd.read_csv(DS / "selected" / "beauty_reviews_selected_100k.csv", usecols=["review_id"])
    assert len(sel) == 100000 and len(train) == 80000 and len(test) == 20000
    assert not set(train.review_id) & set(test.review_id)
    assert not set(train.text) & set(test.text)
    assert "user_id" not in train.columns and "images" not in train.columns
    assert set(train.label_type) == {"RATING_DERIVED"}


def test_sentiment_predictions():
    pos = analyze_sentiment("I love this moisturizer, it works great and smells wonderful.", "Great")
    neg = analyze_sentiment("Terrible product, broke me out and a complete waste of money.", "Awful")
    assert pos["status"] == "ok" and pos["sentiment"] == "positive"
    assert neg["status"] == "ok" and neg["sentiment"] == "negative"
    assert 0.0 <= pos["confidence"] <= 1.0 and pos["model_version"]


def test_empty_input_handled():
    assert analyze_sentiment("   ", None)["status"] == "invalid_input"
    assert analyze_sentiment(None)["status"] == "invalid_input"


def test_authenticity_not_validated_and_no_synthetic_claims():
    res = analyze_product_reviews(product_id="P001", brand_name="Colourpop")
    assert res["authenticity_analysis_status"] == "NOT_VALIDATED"
    assert res["review_authenticity_score"] is None
    assert "label_breakdown" not in res and "deceptive_review_percentage" not in res
    assert res["marketplace_sentiment"]["status"] == "NO_REVIEW_TEXT_AVAILABLE"
    assert "synthetic_benchmark" not in res


def test_synthetic_benchmark_only_when_explicit():
    res = analyze_product_reviews(product_id="P001", brand_name="Colourpop", include_synthetic_benchmark=True)
    if "synthetic_benchmark" in res:
        assert res["synthetic_benchmark"]["data_scope"] == "SYNTHETIC_BENCHMARK"


def test_real_review_text_sentiment_flow():
    res = analyze_product_reviews(real_reviews=[{"text": "Absolutely love it, fantastic quality."}])
    assert res["marketplace_sentiment"]["analyzed_count"] == 1
    assert res["marketplace_sentiment"]["counts"]["positive"] == 1


def test_classify_review_sentiment_has_no_fake_label():
    res = classify_review_sentiment("Bad", "This was awful and useless.")
    assert res["authenticity_analysis_status"] == "NOT_VALIDATED"
    assert "is_deceptive" not in res and "label_prediction" not in res


def test_api_review_endpoints():
    response = client.get("/api/reviews/P001")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["authenticity_analysis_status"] == "NOT_VALIDATED"

    for path in ("/api/reviews/sentiment", "/api/reviews/classify"):
        r = client.post(path, json={"headline": "Great", "body": "Love this product, works perfectly."})
        assert r.status_code == 200
        assert r.json()["data"]["sentiment"] == "positive"

    bad = client.post("/api/reviews/sentiment", json={"body": ""})
    assert bad.json()["data"]["status"] == "invalid_input"
