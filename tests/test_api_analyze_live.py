"""
Live Test Script for POST /api/analyze route using direct FastAPI endpoint invocation with valid PIL Image.
"""

import sys
import io
import json
from pathlib import Path
from PIL import Image
from fastapi import UploadFile

BASE_DIR = Path(__file__).parent.parent.resolve()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR / "ai-service") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "ai-service"))

from app.main import get_health
from app.routes.analysis import analyze_image
from database.connection import SessionLocal

def create_valid_test_image_bytes() -> bytes:
    """Generates a valid 200x200 RGB JPEG image in bytes."""
    img = Image.new("RGB", (200, 200), color=(230, 50, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def test_api_analyze_live_endpoint():
    import asyncio
    # 1. Health check
    health_resp = asyncio.run(get_health())
    assert health_resp.get("status") == "ok" or health_resp.get("service") == "ai-service"
    print(f"  [1/2] /health OK -> {health_resp}")

    # 2. Analyze route test with valid generated JPEG image bytes
    valid_image_bytes = create_valid_test_image_bytes()
    upload = UploadFile(
        filename="sample_product.jpg",
        file=io.BytesIO(valid_image_bytes),
        headers={"content-type": "image/jpeg"},
    )
    db = SessionLocal()
    try:
        response = analyze_image(file=upload, db=db)
        assert response.status_code == 200
        data = json.loads(response.body.decode("utf-8")) if hasattr(response, "body") else response

        assert data["success"] is True
        assert data["filename"] == "sample_product.jpg"
        assert "ocr_status" in data
        assert "product_detection" in data
        assert "clip_similarity" in data
        assert "review_authenticity" in data
        assert "authenticity_prediction" in data
        assert "product_identity" in data
        assert "marketplace_listings" in data
        assert "platform_comparison" in data
        assert data["db_persisted"] is True
        assert "is_confirmed" in data
        assert "identity_status" in data
        assert "visual_similarity_disclaimer" in data

        print("  [2/2] POST /api/analyze OK -> Response schema intact and db_persisted=True!")
        print("\nALL FASTAPI ROUTE TESTS PASSED SUCCESSFULLY!")
    finally:
        db.close()

if __name__ == "__main__":
    test_api_analyze_live_endpoint()
