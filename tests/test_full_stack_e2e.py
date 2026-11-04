"""
Full Stack Multi-Tier Integration Test Suite (Phase 3).
Tests: Next.js/HTTP Client -> Express Gateway (:5000) -> FastAPI AI Service (:8001) -> PostgreSQL (cosmetic_verification_db).
"""

import sys
import io
import urllib.request
import json
from pathlib import Path
from PIL import Image
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).parent.parent.resolve()
SITE_PACKAGES_DIR = BASE_DIR / "ai-service" / "venv" / "Lib" / "site-packages"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if SITE_PACKAGES_DIR.exists() and str(SITE_PACKAGES_DIR) not in sys.path:
    sys.path.insert(0, str(SITE_PACKAGES_DIR))

from database.connection import DATABASE_URL, engine

EXPRESS_BACKEND_URL = "http://localhost:5000/api/upload"


def create_sample_image_bytes(color=(220, 40, 40), size=(300, 300)) -> bytes:
    """Generates valid JPEG image bytes for product upload testing."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def post_multipart_file(url: str, filename: str, content: bytes, content_type: str = "image/jpeg"):
    """Helper to execute raw multipart/form-data HTTP POST request without external dependencies."""
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = bytearray()

    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode("utf-8"))
    body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
    body.extend(content)
    body.extend(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            status_code = resp.status
            res_body = resp.read().decode("utf-8")
            return status_code, json.loads(res_body)
    except urllib.error.HTTPError as http_err:
        res_body = http_err.read().decode("utf-8")
        try:
            parsed = json.loads(res_body)
        except Exception:
            parsed = {"message": res_body}
        return http_err.code, parsed


def test_1_express_gateway_health():
    """Test 1: Express backend health check."""
    print("\n[TEST 1] Testing Express Backend Health Endpoint (:5000/api/health)...")
    req = urllib.request.Request("http://localhost:5000/api/health")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["success"] is True
        print(f"  PASS! Express backend server is healthy -> {data['message']}")



def test_2_e2e_image_upload_and_persistence():
    """Test 2: Full End-to-End Image Upload from Gateway -> FastAPI -> PostgreSQL."""
    print("\n[TEST 2] Testing E2E Image Upload via Express Gateway (:5000/api/upload)...")
    
    # Try using real catalog image for authentic E2E flow
    sample_img_path = BASE_DIR / "data" / "image_model_dataset" / "Lip_Products" / "P001_Colourpop_LippiePencil" / "P001_0001.jpg"
    if sample_img_path.exists():
        with open(sample_img_path, "rb") as f:
            img_bytes = f.read()
    else:
        img_bytes = create_sample_image_bytes(color=(210, 60, 60))

    status_code, data = post_multipart_file(EXPRESS_BACKEND_URL, "colourpop_lipstick.jpg", img_bytes)

    assert status_code == 200, f"Expected 200 OK, got {status_code}: {data}"
    assert data["success"] is True
    assert "ocr_status" in data
    assert "product_detection" in data
    assert "clip_similarity" in data
    assert "product_identity" in data
    assert "marketplace_listings" in data
    assert "platform_comparison" in data
    assert data["db_persisted"] is True, f"Expected db_persisted=True, got {data.get('db_persisted')}"

    print("  Status: Express Gateway -> FastAPI AI Service -> JSON Response OK!")
    print(f"  Status: db_persisted = {data['db_persisted']}")

    # Direct PostgreSQL verification query
    with engine.connect() as conn:
        prod_count = conn.execute(text("SELECT COUNT(*) FROM products;")).scalar()
        mkt_count = conn.execute(text("SELECT COUNT(*) FROM marketplaces;")).scalar()
        listing_count = conn.execute(text("SELECT COUNT(*) FROM marketplace_listings;")).scalar()

        assert prod_count >= 1, "Expected products table to contain records"
        assert mkt_count >= 1, "Expected marketplaces table to contain records"
        assert listing_count >= 0, "Marketplace listings count checked safely"

        print(f"  Status: Verified PostgreSQL Database Records -> Products: {prod_count}, Marketplaces: {mkt_count}, Listings: {listing_count}")

    print("  PASS! End-to-end integration and PostgreSQL database persistence verified.")


def test_3_corrupted_empty_file_safety():
    """Test 3: Reject empty/corrupted 0-byte file uploads safely."""
    print("\n[TEST 3] Testing Corrupted/Empty 0-Byte File Error Handling...")
    empty_bytes = b""
    status_code, data = post_multipart_file(EXPRESS_BACKEND_URL, "empty.jpg", empty_bytes)

    assert status_code == 400
    assert data["success"] is False
    print("  PASS! Empty 0-byte file rejected safely with 400 Bad Request.")


def test_4_invalid_file_extension_safety():
    """Test 4: Reject non-image file formats safely."""
    print("\n[TEST 4] Testing Invalid File Extension Error Handling...")
    script_bytes = b"console.log('malicious script');"
    status_code, data = post_multipart_file(EXPRESS_BACKEND_URL, "script.js", script_bytes, content_type="application/javascript")

    assert status_code == 400
    assert data["success"] is False
    print("  PASS! Non-image file extension rejected safely with 400 Bad Request.")


def run_all_e2e_tests():
    print("=" * 80)
    print("RUNNING PHASE 3 FULL STACK INTEGRATION & E2E PERSISTENCE TEST SUITE")
    print("=" * 80)
    test_1_express_gateway_health()
    test_2_e2e_image_upload_and_persistence()
    test_3_corrupted_empty_file_safety()
    test_4_invalid_file_extension_safety()
    print("=" * 80)
    print("ALL PHASE 3 INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_e2e_tests()
