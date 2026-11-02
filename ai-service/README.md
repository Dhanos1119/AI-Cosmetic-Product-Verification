# CosmeticVerify — AI Service (FastAPI)

FastAPI microservice for image verification, Pillow/OpenCV image inspection, OCR text extraction, and CLIP model predictions for the **AI Cosmetic Product Verification** system.

---

## 🛠️ Requirements & Installation

1. Navigate to the `ai-service` directory:
   ```bash
   cd ai-service
   ```

2. Create and activate a Python virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Running the AI Service

Start the FastAPI server on port **8000**:

```bash
# Using uvicorn directly:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or using Python:
python app/main.py
```

- **Local Access**: `http://localhost:8000`
- **Network Access**: `http://192.168.1.27:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`

---

## 📡 API Endpoints

### 1. Health Check
`GET /health`

**Response:**
```json
{
  "status": "ok",
  "service": "AI Cosmetic Verification Service"
}
```

### 2. Analyze Image
`POST /api/analyze`

Send a `multipart/form-data` request with field name `file`.

**Curl Example:**
```bash
curl -X POST -F "file=@/path/to/product_image.jpg" http://192.168.1.27:8000/api/analyze
```

**Response (`200 OK`):**
```json
{
  "success": true,
  "filename": "product_image.jpg",
  "image_validation": "valid",
  "width": 1516,
  "height": 1037,
  "format": "JPEG",
  "size": 327680,
  "ocr_status": "pending",
  "product_detection": "pending",
  "clip_similarity": "pending",
  "review_authenticity": "pending",
  "authenticity_prediction": "pending"
}
```
