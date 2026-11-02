import sys
import json
from pathlib import Path

BASE_DIR = Path('c:/Users/Dhanoshigan Ratnaraj/AI-Cosmetic-Product-Verification')
sys.path.insert(0, str(BASE_DIR / 'ai-service'))

from fastapi.testclient import TestClient
from app.main import app
from app.schemas.response import AnalysisResponse

client = TestClient(app)

# Pick a real dataset image
img_path = BASE_DIR / 'data' / 'image_model_dataset' / 'Lip_Products' / 'P001_Colourpop_LippiePencil' / 'P001_0001.jpg'
with open(img_path, 'rb') as f:
    img_bytes = f.read()

# Make POST request to /api/analyze endpoint
response = client.post(
    '/api/analyze',
    files={'file': ('P001_0001.jpg', img_bytes, 'image/jpeg')}
)

print('HTTP Status Code:', response.status_code)
data = response.json()

# Schema Validation with Pydantic AnalysisResponse model
validated = AnalysisResponse(**data)
print('Pydantic Schema Validation: PASSED!')

print('\n--- API Smoke Test Output Summary ---')
print('Filename:', data.get('filename'))
print('OCR Status:', data.get('ocr_status'))
print('OCR Extracted Brand:', data.get('brand_name'))
print('OCR Extracted Product:', data.get('product_name'))
print('Product Detection:', data.get('product_detection'))
print('CLIP Similarity Summary:', data.get('clip_similarity'))

clip = data.get('clip_result', {})
print('\nCLIP Matched Product ID:', clip.get('matched_product_id'))
print('CLIP Matched Product Name:', clip.get('matched_product_name'))
print('CLIP Matched Brand:', clip.get('matched_brand'))
print('Similarity Score:', clip.get('similarity_score'))
print('Similarity Percentage:', clip.get('similarity_percentage'), '%')
print('Match Status:', clip.get('match_status'))
print('Confidence Level:', clip.get('confidence_level'))
print('Model:', clip.get('model'))

print('\n--- Top 5 Matching Candidates ---')
for m in clip.get('top_matches', []):
    print(f"Rank #{m['rank']}: Product {m['product_id']} ({m['brand']} - {m['product_name']}) -> {m['similarity_percentage']}%")
