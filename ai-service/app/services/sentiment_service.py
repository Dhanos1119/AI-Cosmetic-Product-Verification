"""
Review Sentiment Service (Phase 8)

Loads the persisted TF-IDF + Logistic Regression baseline from models/review_sentiment/
and predicts positive / neutral / negative sentiment for actual review text.

IMPORTANT
  - The model is trained on RATING-DERIVED labels (1-2 negative, 3 neutral, 4-5 positive)
    from the Amazon Beauty Reviews dataset. It is a sentiment model, NOT a fake-review detector.
  - The model is loaded once (lazily) and NEVER retrained during requests.
  - Only analyze review text that genuinely comes from a documented source.
"""

import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib

logger = logging.getLogger("ai_service.sentiment")

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_DIR = BASE_DIR / "models" / "review_sentiment"
VECTORIZER_PATH = MODEL_DIR / "tfidf_vectorizer.joblib"
CLASSIFIER_PATH = MODEL_DIR / "sentiment_logistic_regression.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

MAX_TEXT_CHARS = 20_000

_lock = threading.Lock()
_cache: Dict[str, Any] = {"vectorizer": None, "classifier": None, "metadata": None, "loaded": False}


def _load_model() -> bool:
    """Loads persisted artifacts once. Returns True if the model is available."""
    if _cache["loaded"]:
        return True
    with _lock:
        if _cache["loaded"]:
            return True
        if not (VECTORIZER_PATH.exists() and CLASSIFIER_PATH.exists()):
            logger.warning(f"Sentiment model artifacts not found in {MODEL_DIR}")
            return False
        try:
            _cache["vectorizer"] = joblib.load(VECTORIZER_PATH)
            _cache["classifier"] = joblib.load(CLASSIFIER_PATH)
            if METADATA_PATH.exists():
                with open(METADATA_PATH, "r", encoding="utf-8") as f:
                    _cache["metadata"] = json.load(f)
            _cache["loaded"] = True
            logger.info("Loaded review sentiment model v%s", get_model_version())
            return True
        except Exception as exc:
            logger.error(f"Failed to load sentiment model: {exc}")
            return False


def get_model_version() -> str:
    meta = _cache.get("metadata") or {}
    return str(meta.get("model_version", "unknown"))


def get_model_info() -> Dict[str, Any]:
    """Returns model metadata with an explicit scope disclaimer."""
    available = _load_model()
    meta = _cache.get("metadata") or {}
    return {
        "available": available,
        "model_version": get_model_version() if available else None,
        "label_type": meta.get("label_type", "RATING_DERIVED"),
        "task": "rating-derived sentiment classification (positive/neutral/negative)",
        "is_fake_review_detector": False,
        "training_dataset": meta.get("dataset_source"),
        "train_rows": meta.get("train_rows"),
        "test_rows": meta.get("test_rows"),
    }


def _unavailable(reason: str) -> Dict[str, Any]:
    return {
        "status": "unavailable",
        "sentiment": None,
        "confidence": None,
        "probabilities": None,
        "model_version": None,
        "label_type": "RATING_DERIVED",
        "reason": reason,
    }


def analyze_sentiment(text: Optional[str], title: Optional[str] = None) -> Dict[str, Any]:
    """
    Predicts sentiment for one review. Returns status 'ok', 'invalid_input' or 'unavailable'.
    Confidence is the model's predicted class probability (not a calibrated accuracy).
    """
    title_s = title.strip() if isinstance(title, str) else ""
    text_s = text.strip() if isinstance(text, str) else ""
    combined = f"{title_s} {text_s}".strip()
    if not text_s and not title_s:
        return _unavailable("Empty or invalid review text.") | {"status": "invalid_input"}
    if not _load_model():
        return _unavailable("Sentiment model artifacts are not available.")

    try:
        vec = _cache["vectorizer"].transform([combined[:MAX_TEXT_CHARS]])
        clf = _cache["classifier"]
        probs = clf.predict_proba(vec)[0]
        idx = int(probs.argmax())
        return {
            "status": "ok",
            "sentiment": str(clf.classes_[idx]),
            "confidence": round(float(probs[idx]), 4),
            "probabilities": {str(c): round(float(p), 4) for c, p in zip(clf.classes_, probs)},
            "model_version": get_model_version(),
            "label_type": "RATING_DERIVED",
        }
    except Exception as exc:
        logger.error(f"Sentiment prediction failed: {exc}")
        return _unavailable("Sentiment prediction failed.")


def analyze_review_batch(reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes a list of ACTUAL reviews (dicts with 'title'/'headline' and 'text'/'comment'/'body').
    Returns per-review sentiment plus counts. Returns zero counts when no usable text exists.
    """
    results = []
    counts = {"positive": 0, "neutral": 0, "negative": 0}
    for r in reviews or []:
        text = r.get("text") or r.get("comment") or r.get("body")
        title = r.get("title") or r.get("headline")
        res = analyze_sentiment(text, title)
        results.append(res)
        if res["status"] == "ok":
            counts[res["sentiment"]] += 1
    analyzed = sum(counts.values())
    return {
        "analyzed_count": analyzed,
        "counts": counts,
        "results": results,
        "model_version": get_model_version() if _cache["loaded"] else None,
    }
