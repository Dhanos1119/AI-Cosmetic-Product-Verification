"""
Multi-Product CLIP API Smoke Test Runner

Tests 7 representative product images (P001, P005, P010, P015, P020, P025, P030)
via the actual `/api/analyze` FastAPI endpoint.

Saves output to tests/results/clip_api_smoke_test_results.json
"""

import sys
import json
import time
from pathlib import Path

# Force UTF-8 encoding for stdout on Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).parent.parent.resolve()
AI_SERVICE_DIR = BASE_DIR / "ai-service"
RESULTS_DIR = BASE_DIR / "tests" / "results"

if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from fastapi.testclient import TestClient
from app.main import app

def run_multi_product_smoke_test():
    print("=" * 75)
    print("RUNNING MULTI-PRODUCT CLIP API SMOKE TEST (POST /api/analyze)")
    print("=" * 75)

    client = TestClient(app)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    json_out_file = RESULTS_DIR / "clip_api_smoke_test_results.json"

    dataset_dir = BASE_DIR / "data" / "image_model_dataset"
    target_pids = ["P001", "P005", "P010", "P015", "P020", "P025", "P030"]

    # Discover target image files
    test_image_map = {}
    for cat_dir in dataset_dir.iterdir():
        if not cat_dir.is_dir() or cat_dir.name.startswith('_'):
            continue
        for folder in cat_dir.iterdir():
            if not folder.is_dir():
                continue
            pid = folder.name.split('_')[0]
            if pid in target_pids:
                imgs = sorted([f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']], key=lambda x: x.name)
                if imgs:
                    test_image_map[pid] = imgs[0]  # Pick first image

    test_results = []
    correct_count = 0
    total_count = len(target_pids)

    for idx, pid in enumerate(target_pids, start=1):
        img_path = test_image_map.get(pid)
        if not img_path or not img_path.exists():
            print(f"[{idx}/7] Product {pid}: Image file NOT FOUND!")
            continue

        with open(img_path, 'rb') as f:
            file_bytes = f.read()

        t0 = time.time()
        response = client.post(
            "/api/analyze",
            files={"file": (img_path.name, file_bytes, "image/jpeg")}
        )
        elapsed_sec = round(time.time() - t0, 3)

        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
        res_data = response.json()

        clip = res_data.get("clip_result", {})
        ocr = res_data.get("ocr_result", {})
        predicted_pid = clip.get("matched_product_id", "UNKNOWN")
        is_correct = (predicted_pid == pid)

        if is_correct:
            correct_count += 1
            status_badge = "[PASS]"
        else:
            status_badge = "[FAIL]"

        print(f"[{idx}/7] Expected: {pid} | Predicted: {predicted_pid} | Sim: {clip.get('similarity_percentage', 0)}% | Time: {elapsed_sec}s | {status_badge}")

        record = {
            "test_index": idx,
            "image_filename": img_path.name,
            "relative_path": str(img_path.relative_to(BASE_DIR)).replace('\\', '/'),
            "expected_product_id": pid,
            "predicted_product_id": predicted_pid,
            "is_correct": is_correct,
            "similarity_score": clip.get("similarity_score"),
            "similarity_percentage": clip.get("similarity_percentage"),
            "match_status": clip.get("match_status"),
            "confidence_level": clip.get("confidence_level"),
            "processing_time_seconds": elapsed_sec,
            "ocr_extracted_raw_text": ocr.get("raw_text", []),
            "ocr_brand_name": ocr.get("brand_name"),
            "ocr_product_name": ocr.get("product_name"),
            "top_5_product_matches": [
                {
                    "rank": m.get("rank"),
                    "product_id": m.get("product_id"),
                    "brand": m.get("brand"),
                    "product_name": m.get("product_name"),
                    "category": m.get("category"),
                    "similarity_percentage": m.get("similarity_percentage")
                }
                for m in clip.get("top_matches", [])
            ]
        }
        test_results.append(record)

    accuracy_pct = round((correct_count / total_count) * 100, 1)

    output_payload = {
        "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model_name": "OpenAI CLIP ViT-B/32 Vision Transformer (Hugging Face)",
        "endpoint_tested": "POST /api/analyze",
        "total_images_tested": total_count,
        "correct_predictions": correct_count,
        "failed_predictions": total_count - correct_count,
        "accuracy_percentage": accuracy_pct,
        "results": test_results
    }

    with open(json_out_file, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    print(f"\nSaved smoke test results to: {json_out_file}")

    print("\n" + "=" * 75)
    print("MULTI-PRODUCT API SMOKE TEST SUMMARY")
    print("=" * 75)
    print(f"Total Target Products Tested: {total_count}")
    print(f"Correct Predictions (Top-1 Match): {correct_count} / {total_count} ({accuracy_pct}%)")
    print(f"Failed Predictions: {total_count - correct_count} / {total_count}")
    print("-" * 75)
    for r in test_results:
        status = "[PASS]" if r["is_correct"] else "[FAIL]"
        print(f"  {r['expected_product_id']} ({r['image_filename']}): Predicted {r['predicted_product_id']} ({r['similarity_percentage']}%) -> {status}")
    print("=" * 75)

if __name__ == "__main__":
    run_multi_product_smoke_test()
