"""
Phase 8 — Real Amazon Beauty Review Dataset Preparation & Sentiment Baseline Training

Input : data/review_dataset/raw/amazon_beauty_reviews_dataset.csv  (701,528 rows, untouched)
Output:
  data/review_dataset/selected/beauty_reviews_selected_100k.csv
  data/review_dataset/processed/beauty_reviews_prepared_100k.csv
  data/review_dataset/train/beauty_reviews_train_80k.csv
  data/review_dataset/test/beauty_reviews_test_20k.csv
  models/review_sentiment/tfidf_vectorizer.joblib
  models/review_sentiment/sentiment_logistic_regression.joblib
  models/review_sentiment/model_metadata.json
  models/review_sentiment/evaluation_report.json

SAFETY RULES
  - Original CSV is opened READ-ONLY and never modified.
  - Existing synthetic benchmark files (reviews_100k.db, reviews_100k_dataset.jsonl.gz) are preserved.
  - Existing CLIP/OCR model artifacts are never touched.
  - PostgreSQL tables are not accessed.
  - All file writes go to new paths only.

LABEL METHODOLOGY (rating-derived, NOT ground-truth fake/real labels)
  rating 1-2  -> sentiment = 'negative'
  rating 3    -> sentiment = 'neutral'
  rating 4-5  -> sentiment = 'positive'
  source_dataset = 'amazon_beauty_reviews_dataset'
  label_type = 'RATING_DERIVED'
"""

import os
import sys
import json
import time
import hashlib
import logging
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)
import joblib

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_CSV  = BASE_DIR / "data" / "review_dataset" / "raw" / "amazon_beauty_reviews_dataset.csv"

SELECTED_DIR  = BASE_DIR / "data" / "review_dataset" / "selected"
PROCESSED_DIR = BASE_DIR / "data" / "review_dataset" / "processed"
TRAIN_DIR     = BASE_DIR / "data" / "review_dataset" / "train"
TEST_DIR      = BASE_DIR / "data" / "review_dataset" / "test"
MODEL_DIR     = BASE_DIR / "models" / "review_sentiment"

SELECTED_CSV  = SELECTED_DIR  / "beauty_reviews_selected_100k.csv"
PREPARED_CSV  = PROCESSED_DIR / "beauty_reviews_prepared_100k.csv"
TRAIN_CSV     = TRAIN_DIR     / "beauty_reviews_train_80k.csv"
TEST_CSV      = TEST_DIR      / "beauty_reviews_test_20k.csv"

VECTORIZER_PATH  = MODEL_DIR / "tfidf_vectorizer.joblib"
CLASSIFIER_PATH  = MODEL_DIR / "sentiment_logistic_regression.joblib"
METADATA_PATH    = MODEL_DIR / "model_metadata.json"
EVAL_REPORT_PATH = MODEL_DIR / "evaluation_report.json"

RANDOM_SEED   = 42
TARGET_SAMPLE = 100_000
TRAIN_SIZE    = 80_000
TEST_SIZE     = 20_000

# Required source columns
REQUIRED_COLS = [
    "rating", "title", "text", "images",
    "asin", "parent_asin", "user_id",
    "timestamp", "helpful_vote", "verified_purchase"
]

# Columns kept in model dataset (images and user_id excluded)
MODEL_COLS = [
    "review_id", "asin", "parent_asin", "title", "text",
    "rating", "verified_purchase", "timestamp", "helpful_vote",
    "sentiment", "source_dataset", "label_type"
]

SENTIMENT_MAP = {1: "negative", 2: "negative", 3: "neutral", 4: "positive", 5: "positive"}


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("phase8")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def row_fingerprint(row: pd.Series) -> str:
    """SHA-256 fingerprint of (asin, user_id, text) for duplicate detection."""
    raw = f"{row['asin']}|{row['user_id']}|{str(row['text'])}"
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()


def derive_sentiment(rating: int) -> str:
    return SENTIMENT_MAP.get(int(rating), "neutral")


# ---------------------------------------------------------------------------
# Phase A — Load and validate CSV
# ---------------------------------------------------------------------------
def load_and_clean_csv() -> pd.DataFrame:
    log.info("=" * 70)
    log.info("PHASE A — Loading Amazon Beauty Reviews CSV (read-only)")
    log.info("=" * 70)
    log.info(f"Source: {RAW_CSV}")

    if not RAW_CSV.exists():
        log.error(f"Raw CSV not found at {RAW_CSV}")
        sys.exit(1)

    # Read in 50k-row chunks, concat. Low memory, no copy of images into RAM.
    chunk_list = []
    chunk_size = 50_000
    total_rows = 0
    log.info("Chunked read in progress ...")
    for chunk in pd.read_csv(RAW_CSV, chunksize=chunk_size, low_memory=False, encoding="utf-8"):
        total_rows += len(chunk)
        chunk_list.append(chunk)

    df = pd.concat(chunk_list, ignore_index=True)
    log.info(f"Loaded {len(df):,} rows, {len(df.columns)} columns")

    # Validate expected columns exist
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        log.error(f"Missing expected columns: {missing}")
        sys.exit(1)
    log.info(f"All required columns present: {REQUIRED_COLS}")

    # --- Inspect timestamp format before any conversion ---
    ts_sample = df["timestamp"].dropna().head(5).tolist()
    log.info(f"Timestamp samples (raw): {ts_sample}")

    return df


# ---------------------------------------------------------------------------
# Phase B — Deduplication and eligibility filtering
# ---------------------------------------------------------------------------
def filter_eligible(df: pd.DataFrame) -> pd.DataFrame:
    log.info("=" * 70)
    log.info("PHASE B — Deduplication and eligibility filtering")
    log.info("=" * 70)

    initial = len(df)

    # 1. Remove rows with null or whitespace-only text
    df = df.dropna(subset=["text"])
    df = df[df["text"].astype(str).str.strip().str.len() > 0]
    after_null = len(df)
    log.info(f"After null/empty text removal: {after_null:,} rows (removed {initial - after_null:,})")

    # 2. Validate ratings are in 1-5
    df = df[df["rating"].isin([1, 2, 3, 4, 5])]
    after_rating = len(df)
    log.info(f"After invalid rating removal: {after_rating:,} rows (removed {after_null - after_rating:,})")

    # 3. Exact full-row duplicate removal (same row repeated byte-for-byte)
    before_exact = len(df)
    df = df.drop_duplicates()
    after_exact = len(df)
    exact_dupes = before_exact - after_exact
    log.info(f"Exact row duplicates removed: {exact_dupes:,} (now {after_exact:,} rows)")

    # 4. Semantic duplicate removal: same (asin, user_id, text)
    before_sem = len(df)
    df = df.drop_duplicates(subset=["asin", "user_id", "text"])
    after_sem = len(df)
    sem_dupes = before_sem - after_sem
    log.info(f"(asin, user_id, text) duplicates removed: {sem_dupes:,} (now {after_sem:,} rows)")

    # 4b. Exact-text duplicate removal across ALL products/users (keep first occurrence).
    # Decision: prevents identical review text appearing in both train and test (leakage).
    before_txt = len(df)
    df = df.drop_duplicates(subset=["text"])
    log.info(f"Exact-text duplicates removed (global, keep first): {before_txt - len(df):,} (now {len(df):,} rows)")

    # 5. Require non-empty title (allow NaN — will be replaced with empty string for model)
    # Decision: keep rows with null titles; fill empty string during model training
    null_title = df["title"].isna().sum()
    log.info(f"Rows with null titles (kept, filled with '' during training): {null_title:,}")

    log.info(f"Eligible pool size: {len(df):,} rows")
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Phase C — Stratified 100k sampling
# ---------------------------------------------------------------------------
def sample_100k(df: pd.DataFrame) -> pd.DataFrame:
    log.info("=" * 70)
    log.info("PHASE C — Stratified sampling of exactly 100,000 reviews")
    log.info("=" * 70)

    # Derive sentiment label on full eligible pool first
    df["sentiment"] = df["rating"].apply(derive_sentiment)

    # Sentiment class distribution
    dist = df["sentiment"].value_counts()
    log.info(f"Eligible pool distribution:\n{dist.to_string()}")

    eligible = len(df)
    if eligible < TARGET_SAMPLE:
        log.error(
            f"Eligible pool ({eligible:,}) is smaller than target ({TARGET_SAMPLE:,}). "
            "Cannot fabricate missing records — aborting."
        )
        sys.exit(1)

    # Stratified sample preserving rating-derived sentiment proportions
    sample_df, _ = train_test_split(
        df,
        train_size=TARGET_SAMPLE,
        stratify=df["sentiment"],
        random_state=RANDOM_SEED,
        shuffle=True
    )
    sample_df = sample_df.reset_index(drop=True)

    # Add metadata columns
    sample_df["review_id"]     = [f"REAL_{i+1:06d}" for i in range(len(sample_df))]
    sample_df["source_dataset"] = "amazon_beauty_reviews_dataset"
    sample_df["label_type"]     = "RATING_DERIVED"

    # Record source fingerprint for traceability
    sample_df["source_fingerprint"] = sample_df.apply(row_fingerprint, axis=1)

    sampled_dist = sample_df["sentiment"].value_counts()
    log.info(f"Sampled 100k distribution:\n{sampled_dist.to_string()}")
    log.info(f"Sampled exactly: {len(sample_df):,} rows")
    assert len(sample_df) == TARGET_SAMPLE, f"Expected {TARGET_SAMPLE}, got {len(sample_df)}"

    return sample_df


# ---------------------------------------------------------------------------
# Phase D — Save selected and prepared CSVs
# ---------------------------------------------------------------------------
def save_selected_and_prepared(sample_df: pd.DataFrame):
    log.info("=" * 70)
    log.info("PHASE D — Saving selected and prepared CSV files")
    log.info("=" * 70)

    for d in [SELECTED_DIR, PROCESSED_DIR, TRAIN_DIR, TEST_DIR, MODEL_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # Selected CSV — all original columns + added metadata columns (NO user_id removal here)
    selected_cols = list(sample_df.columns)
    log.info(f"Writing selected CSV: {SELECTED_CSV}")
    sample_df[selected_cols].to_csv(SELECTED_CSV, index=False, encoding="utf-8")
    log.info(f"  -> {SELECTED_CSV.stat().st_size / 1e6:.2f} MB, {len(sample_df):,} rows")

    # Prepared CSV — model input columns only (no images, no user_id)
    # Add source_fingerprint to prepared for traceability
    prepared_cols = MODEL_COLS + ["source_fingerprint"]
    # Ensure all model cols exist
    for col in MODEL_COLS:
        if col not in sample_df.columns:
            sample_df[col] = ""
    log.info(f"Writing prepared CSV: {PREPARED_CSV}")
    sample_df[prepared_cols].to_csv(PREPARED_CSV, index=False, encoding="utf-8")
    log.info(f"  -> {PREPARED_CSV.stat().st_size / 1e6:.2f} MB, {len(sample_df):,} rows")

    return sample_df[prepared_cols].copy()


# ---------------------------------------------------------------------------
# Phase E — 80k/20k train/test split with leakage checks
# ---------------------------------------------------------------------------
def create_train_test_split(prepared_df: pd.DataFrame):
    log.info("=" * 70)
    log.info("PHASE E — Creating 80,000 / 20,000 stratified train/test split")
    log.info("=" * 70)

    assert len(prepared_df) == TARGET_SAMPLE

    train_df, test_df = train_test_split(
        prepared_df,
        train_size=TRAIN_SIZE,
        test_size=TEST_SIZE,
        stratify=prepared_df["sentiment"],
        random_state=RANDOM_SEED,
        shuffle=True
    )
    train_df = train_df.reset_index(drop=True)
    test_df  = test_df.reset_index(drop=True)

    assert len(train_df) == TRAIN_SIZE, f"Train size error: {len(train_df)}"
    assert len(test_df)  == TEST_SIZE,  f"Test size error:  {len(test_df)}"

    # --- Leakage checks ---
    # 1. review_id overlap (should be zero — each row has a unique review_id)
    id_overlap = set(train_df["review_id"]) & set(test_df["review_id"])
    log.info(f"Review ID overlap (must be 0): {len(id_overlap)}")
    assert len(id_overlap) == 0, "LEAKAGE: review_id overlap detected!"

    # 2. Exact text overlap
    train_texts = set(train_df["text"].dropna().astype(str))
    test_texts  = set(test_df["text"].dropna().astype(str))
    text_overlap = train_texts & test_texts
    log.info(f"Exact text overlap count: {len(text_overlap)} (expected ~0 due to earlier dedup)")

    # 3. ASIN (product) overlap — expected; documented
    asin_overlap = set(train_df["asin"]) & set(test_df["asin"])
    log.info(
        f"ASIN (product) overlap: {len(asin_overlap):,} — "
        "EXPECTED. Split is random-stratified by sentiment, not grouped by product. "
        "Same product may appear in both train and test. This is documented."
    )

    # Distribution check
    log.info(f"Train sentiment distribution:\n{train_df['sentiment'].value_counts().to_string()}")
    log.info(f"Test  sentiment distribution:\n{test_df['sentiment'].value_counts().to_string()}")

    # Save
    log.info(f"Writing train CSV: {TRAIN_CSV}")
    train_df.to_csv(TRAIN_CSV, index=False, encoding="utf-8")
    log.info(f"  -> {TRAIN_CSV.stat().st_size / 1e6:.2f} MB, {len(train_df):,} rows")

    log.info(f"Writing test CSV: {TEST_CSV}")
    test_df.to_csv(TEST_CSV, index=False, encoding="utf-8")
    log.info(f"  -> {TEST_CSV.stat().st_size / 1e6:.2f} MB, {len(test_df):,} rows")

    return train_df, test_df


# ---------------------------------------------------------------------------
# Phase F — Train TF-IDF + Logistic Regression sentiment baseline
# ---------------------------------------------------------------------------
def train_sentiment_model(train_df: pd.DataFrame, test_df: pd.DataFrame) -> dict:
    log.info("=" * 70)
    log.info("PHASE F — Training TF-IDF + Logistic Regression sentiment baseline")
    log.info("=" * 70)

    # Combine title + text (null-safe)
    def combine_text(row):
        t = str(row["title"]) if pd.notna(row["title"]) else ""
        b = str(row["text"])  if pd.notna(row["text"])  else ""
        return (t + " " + b).strip()

    log.info("Preparing training text features ...")
    X_train_raw = train_df.apply(combine_text, axis=1).tolist()
    y_train     = train_df["sentiment"].tolist()

    log.info("Preparing test text features ...")
    X_test_raw  = test_df.apply(combine_text, axis=1).tolist()
    y_test      = test_df["sentiment"].tolist()

    # Vectorizer fit on TRAINING data only
    log.info("Fitting TF-IDF vectorizer on training set only ...")
    vectorizer = TfidfVectorizer(
        max_features=15_000,
        ngram_range=(1, 2),
        stop_words="english",
        sublinear_tf=True,
        min_df=3
    )
    t0 = time.time()
    X_train = vectorizer.fit_transform(X_train_raw)
    log.info(f"Vectorizer fitted. Shape: {X_train.shape}. Time: {time.time()-t0:.1f}s")

    # Transform test data using FITTED vectorizer (no re-fit)
    X_test = vectorizer.transform(X_test_raw)
    log.info(f"Test matrix shape: {X_test.shape}")

    # Train Logistic Regression
    log.info("Training Logistic Regression ...")
    t1 = time.time()
    clf = LogisticRegression(
        C=1.0,
        max_iter=1000,
        solver="saga",
        n_jobs=-1,
        random_state=RANDOM_SEED
    )
    clf.fit(X_train, y_train)
    train_duration = round(time.time() - t1, 2)
    log.info(f"Training complete in {train_duration}s")

    # Evaluate on all 20,000 test records
    log.info("Evaluating on 20,000 test records ...")
    t2 = time.time()
    y_pred = clf.predict(X_test)
    inference_duration = round(time.time() - t2, 4)

    classes = sorted(set(y_test))
    acc     = round(accuracy_score(y_test, y_pred) * 100, 2)
    prec_m  = round(precision_score(y_test, y_pred, average="macro", zero_division=0) * 100, 2)
    rec_m   = round(recall_score(y_test, y_pred, average="macro", zero_division=0) * 100, 2)
    f1_m    = round(f1_score(y_test, y_pred, average="macro", zero_division=0) * 100, 2)

    # Per-class metrics
    per_class_report = {}
    for cls in classes:
        prec_c = round(precision_score(y_test, y_pred, labels=[cls], average="micro", zero_division=0) * 100, 2)
        rec_c  = round(recall_score(y_test, y_pred, labels=[cls], average="micro", zero_division=0) * 100, 2)
        f1_c   = round(f1_score(y_test, y_pred, labels=[cls], average="micro", zero_division=0) * 100, 2)
        per_class_report[cls] = {"precision": prec_c, "recall": rec_c, "f1": f1_c}

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=classes).tolist()

    # Majority-class baseline
    from collections import Counter
    majority_class = Counter(y_train).most_common(1)[0][0]
    majority_preds = [majority_class] * len(y_test)
    majority_acc   = round(accuracy_score(y_test, majority_preds) * 100, 2)

    # Class distribution
    train_dist = train_df["sentiment"].value_counts().to_dict()
    test_dist  = test_df["sentiment"].value_counts().to_dict()

    log.info(f"Accuracy: {acc}%  |  Macro Precision: {prec_m}%  |  Macro Recall: {rec_m}%  |  Macro F1: {f1_m}%")
    log.info(f"Majority-class baseline accuracy: {majority_acc}%")
    log.info(f"Inference time for 20k records: {inference_duration}s")

    # Save artifacts
    log.info(f"Saving vectorizer: {VECTORIZER_PATH}")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, VECTORIZER_PATH, compress=3)

    log.info(f"Saving classifier: {CLASSIFIER_PATH}")
    joblib.dump(clf, CLASSIFIER_PATH, compress=3)

    return {
        "classes": classes,
        "accuracy": acc,
        "macro_precision": prec_m,
        "macro_recall": rec_m,
        "macro_f1": f1_m,
        "per_class": per_class_report,
        "confusion_matrix": {"labels": classes, "matrix": cm},
        "majority_class_baseline_accuracy": majority_acc,
        "majority_class": majority_class,
        "train_duration_seconds": train_duration,
        "inference_duration_20k_seconds": inference_duration,
        "train_distribution": {k: int(v) for k, v in train_dist.items()},
        "test_distribution":  {k: int(v) for k, v in test_dist.items()},
    }


# ---------------------------------------------------------------------------
# Phase G — Save metadata and evaluation report
# ---------------------------------------------------------------------------
def save_metadata(eval_metrics: dict, sample_df: pd.DataFrame):
    log.info("=" * 70)
    log.info("PHASE G — Saving model metadata and evaluation report")
    log.info("=" * 70)

    import sklearn
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    metadata = {
        "model_name": "Amazon Beauty Review Sentiment Baseline",
        "model_version": "1.0.0",
        "training_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "dataset_source": "amazon_beauty_reviews_dataset.csv",
        "dataset_source_path": str(RAW_CSV),
        "total_source_rows": 701_528,
        "total_selected_rows": TARGET_SAMPLE,
        "train_rows": TRAIN_SIZE,
        "test_rows": TEST_SIZE,
        "random_seed": RANDOM_SEED,
        "split_strategy": "random-stratified by sentiment (not grouped by product or reviewer)",
        "selected_columns": MODEL_COLS,
        "excluded_columns": ["images", "user_id"],
        "label_type": "RATING_DERIVED",
        "label_generation_rule": {
            "negative": "rating 1 or 2",
            "neutral":  "rating 3",
            "positive": "rating 4 or 5"
        },
        "vectorizer": {
            "type": "TfidfVectorizer",
            "max_features": 15_000,
            "ngram_range": [1, 2],
            "stop_words": "english",
            "sublinear_tf": True,
            "min_df": 3
        },
        "classifier": {
            "type": "LogisticRegression",
            "C": 1.0,
            "max_iter": 1000,
            "solver": "saga",
            "multiclass": "multinomial (sklearn default for saga)"
        },
        "python_version": py_version,
        "sklearn_version": sklearn.__version__,
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
        "known_limitations": [
            "Labels are rating-derived (RATING_DERIVED), NOT independently human-verified ground truth.",
            "This model predicts rating-derived sentiment (positive/neutral/negative), NOT fake vs genuine reviews.",
            "The model must NEVER be described as a fake-review detector.",
            "Split is random-stratified by sentiment. The same ASIN may appear in both train and test sets.",
            "Exact duplicate rows, (asin,user_id,text) duplicates, and globally identical review texts were removed before sampling to prevent exact-text leakage between train and test.",
            "No near-duplicate (fuzzy) text detection was applied; near-duplicate overlap between train and test may exist.",
            "Source timestamps are preserved as-is. The raw format is truncated (e.g. '08:48.9', mm:ss.f), has no date component, and cannot be converted to a calendar date.",
            "Model is trained on Amazon Beauty category only; domain shift may reduce accuracy on other categories.",
            "verified_purchase, helpful_vote, and rating are NOT used as model input features.",
            "verified_purchase=False is NOT treated as evidence of a fake review.",
            "The authenticity_analysis_status is set to NOT_VALIDATED in the review analysis service.",
        ],
        "artifacts": {
            "vectorizer": str(VECTORIZER_PATH),
            "classifier": str(CLASSIFIER_PATH),
            "metadata": str(METADATA_PATH),
            "evaluation_report": str(EVAL_REPORT_PATH),
            "selected_csv": str(SELECTED_CSV),
            "prepared_csv": str(PREPARED_CSV),
            "train_csv": str(TRAIN_CSV),
            "test_csv": str(TEST_CSV),
        }
    }

    log.info(f"Writing metadata: {METADATA_PATH}")
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    eval_report = {
        "evaluation_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "evaluation_set": "test_20k",
        "evaluation_rows": TEST_SIZE,
        "disclaimer": (
            "These metrics evaluate the model's ability to predict RATING-DERIVED sentiment labels "
            "(negative/neutral/positive). They do NOT measure fake-review detection accuracy. "
            "Labels are derived mechanically from star ratings and are not human-verified."
        ),
        **eval_metrics,
    }

    log.info(f"Writing evaluation report: {EVAL_REPORT_PATH}")
    with open(EVAL_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    log.info("All artifacts saved.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    log.info("=" * 70)
    log.info("PHASE 8 — Real Review Dataset Preparation & Sentiment Model Training")
    log.info("=" * 70)
    t_start = time.time()

    df        = load_and_clean_csv()
    df        = filter_eligible(df)
    sample_df = sample_100k(df)
    prepared  = save_selected_and_prepared(sample_df)
    train_df, test_df = create_train_test_split(prepared)
    eval_metrics      = train_sentiment_model(train_df, test_df)
    save_metadata(eval_metrics, sample_df)

    total = round(time.time() - t_start, 1)
    log.info("=" * 70)
    log.info(f"Phase 8 complete in {total}s")
    log.info(f"  Selected CSV : {SELECTED_CSV}")
    log.info(f"  Prepared CSV : {PREPARED_CSV}")
    log.info(f"  Train CSV    : {TRAIN_CSV}  ({TRAIN_SIZE:,} rows)")
    log.info(f"  Test CSV     : {TEST_CSV}   ({TEST_SIZE:,} rows)")
    log.info(f"  Vectorizer   : {VECTORIZER_PATH}")
    log.info(f"  Classifier   : {CLASSIFIER_PATH}")
    log.info(f"  Metadata     : {METADATA_PATH}")
    log.info(f"  Eval report  : {EVAL_REPORT_PATH}")
    log.info("=" * 70)
    log.info(f"Model accuracy on 20k holdout: {eval_metrics['accuracy']}%  "
             f"(majority-class baseline: {eval_metrics['majority_class_baseline_accuracy']}%)")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
