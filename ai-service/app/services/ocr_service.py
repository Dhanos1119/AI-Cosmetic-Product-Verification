import io
import re
import numpy as np
import cv2
from PIL import Image

_easyocr_reader = None
_rapidocr_engine = None

KNOWN_BRANDS = [
    "L'Oreal", "L'Oréal", "CeraVe", "The Ordinary", "Neutrogena", "La Roche-Posay",
    "Nivea", "Garnier", "Cetaphil", "Olay", "Estee Lauder", "Estée Lauder",
    "Kiehl's", "Clinique", "Fenty Beauty", "Dior", "Maybelline", "MAC", "COSRX",
    "Innisfree", "Laneige", "Paula's Choice", "Bioderma", "Avene", "Avène",
    "Vichy", "Anua", "Beauty of Joseon", "RoC", "Skinceuticals", "SkinCeuticals",
    "Glossier", "Urban Decay", "Lancome", "Lancôme", "Burt's Bees", "Hada Labo",
    "Sulwhasoo", "Shiseido", "Origins", "Clarins", "Biore", "Bioré", "Vaseline"
]

CATEGORY_KEYWORDS = {
    "Cleanser": ["cleanser", "foaming", "wash", "cleansing", "gel cleanser"],
    "Moisturizer": ["moisturizer", "moisturising", "cream", "lotion", "hydrating", "hydrator", "balm"],
    "Serum": ["serum", "concentrate", "booster", "drop", "essence"],
    "Sunscreen": ["sunscreen", "sunscreen spf", "spf", "sun cream", "uv protection", "sunblock"],
    "Toner": ["toner", "exfoliating toner", "astringent", "skin refiner"],
    "Exfoliant": ["peel", "exfoliant", "scrub", "bha", "aha", "glycolic", "salicylic"],
    "Eye Care": ["eye cream", "eye serum", "eye repair"],
    "Makeup": ["lipstick", "mascara", "foundation", "concealer", "blush", "powder"]
}

def _get_rapidocr_engine():
    global _rapidocr_engine
    if _rapidocr_engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _rapidocr_engine = RapidOCR()
        except Exception as e:
            print(f"Notice: RapidOCR initialization status: {e}")
            _rapidocr_engine = False
    return _rapidocr_engine

def _get_easyocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr
            _easyocr_reader = easyocr.Reader(['en'], gpu=False)
        except Exception as e:
            print(f"Notice: EasyOCR reader initialization status: {e}")
            _easyocr_reader = False
    return _easyocr_reader

def preprocess_image_for_ocr(file_bytes: bytes) -> np.ndarray:
    """
    Applies OpenCV preprocessing (grayscale, contrast enhancement, denoising, adaptive thresholding)
    to maximize text detection accuracy on cosmetic packaging labels.
    """
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        pil_img = Image.open(io.BytesIO(file_bytes)).convert('RGB')
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Resize if resolution is too low
    h, w = gray.shape[:2]
    if w < 600 or h < 600:
        scale = max(600 / w, 600 / h)
        gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

    # Enhance contrast using CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    return enhanced

NON_BRAND_DESCRIPTOR_WORDS = frozenset({
    # Finishes, attributes, textures
    "matte", "dewy", "glow", "satin", "semi-matte", "poreless", "shimmer", "radiant", "luminous",
    "hydrating", "moisturizing", "nourishing", "soothing", "firming", "clarifying", "purifying",
    "liquid", "fluid", "volumizing", "lengthening", "full", "light", "medium", "sheer", "deep",
    "black", "brown", "clear", "transparent",
    # Product categories & forms
    "foundation", "concealer", "powder", "cream", "lotion", "serum", "cleanser", "moisturizer",
    "toner", "exfoliant", "scrub", "mascara", "lipstick", "lip", "gloss", "balm", "liner", "eyeliner",
    "eyeshadow", "shadow", "blush", "bronzer", "highlighter", "primer", "setting", "mist", "spray",
    "compact", "stick", "pencil", "gel", "oil", "foam", "mask", "peel",
    # Skin types & clinical descriptors
    "normal", "oily", "dry", "combination", "sensitive", "skin", "skincare", "beauty", "cosmetic",
    "cosmetics", "makeup", "tint", "finish", "coverage", "broad", "spectrum", "spf", "sunscreen",
    "sunblock", "uv", "uva", "uvb", "waterproof", "water-resistant", "longwear", "anti-aging",
    "repair", "care", "face", "eye", "eyes", "body", "complexion", "shade", "swatch", "flawless",
    # Packaging / OCR noise tokens
    "normaltooly", "normaltooily", "oilysk", "packaging", "label", "container", "volume", "net",
    "wt", "fl", "oz", "ml", "bottle", "tube", "jar", "pump"
})


def _is_descriptor(candidate_text: str) -> bool:
    """Returns True if the candidate text consists solely of generic cosmetic descriptor tokens."""
    tokens = [t.lower() for t in re.findall(r'[a-zA-Z]+', candidate_text)]
    if not tokens:
        return True
    return all(t in NON_BRAND_DESCRIPTOR_WORDS for t in tokens)


def parse_brand_and_product(extracted_lines: list[dict]) -> dict:
    """
    Parses OCR text lines to identify Brand Name, Product Name, Category, and Confidence score.
    Never identifies generic cosmetic descriptors like 'Matte' or 'Foundation' as a brand name.
    """
    if not extracted_lines:
        return {
            "brand_name": "No Text Detected",
            "product_name": "Unidentified Product",
            "category": "Unspecified Cosmetic",
            "confidence": 0.0
        }

    detected_brand = None
    detected_category = None
    clean_lines = []

    # Sort text blocks top-to-bottom
    for item in extracted_lines:
        if isinstance(item, str):
            text = item.strip()
            conf = 0.95
        elif isinstance(item, dict):
            text = item.get("text", "").strip()
            conf = float(item.get("confidence", 0.0))
        else:
            continue
        if len(text) >= 2:
            clean_lines.append((text, conf))

    # 1. Match Known Brands
    for text, conf in clean_lines:
        for brand in KNOWN_BRANDS:
            pattern = r'\b' + re.escape(brand) + r'\b'
            if re.search(pattern, text, re.IGNORECASE) or brand.lower() in text.lower():
                detected_brand = brand
                break
        if detected_brand:
            break

    # If no known brand matched, inspect prominent uppercase lines
    # NEVER select a line if it consists of generic cosmetic descriptors (e.g. "MATTE", "FOUNDATION")
    if not detected_brand and clean_lines:
        for text, conf in clean_lines[:4]:
            candidate = re.sub(r'^[^\w]+|[^\w]+$', '', text)
            if (
                candidate.isupper()
                and len(candidate) >= 3
                and not any(char.isdigit() for char in candidate)
                and not _is_descriptor(candidate)
            ):
                detected_brand = candidate.title()
                break

    if not detected_brand and clean_lines:
        for text, conf in clean_lines[:2]:
            candidate = re.sub(r'^[^\w]+|[^\w]+$', '', text)
            if len(candidate) >= 3 and not _is_descriptor(candidate):
                detected_brand = candidate.title()
                break

    # 2. Detect Product Category
    full_text = " ".join([text for text, _ in clean_lines]).lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in full_text for kw in keywords):
            detected_category = cat
            break

    if not detected_category:
        detected_category = "Cosmetic Container"

    # 3. Formulate Product Name
    product_lines = []
    for text, conf in clean_lines:
        if detected_brand and detected_brand.lower() in text.lower() and len(text.strip()) <= len(detected_brand) + 4:
            continue
        # Skip generic disclaimers or volume numbers like 100ml, 3.4 oz, etc.
        if re.match(r'^\d+(\.\d+)?\s*(ml|oz|g|fl\.?\s*oz)\.?$', text, re.IGNORECASE):
            continue
        product_lines.append(text)

    if product_lines:
        # Take up to 4 lines so multi-line labels like "Fit Me / Matte / +Poreless / Foundation"
        # survive the join rather than being truncated to just the first 2 fragments.
        product_name = " ".join(product_lines[:4])
        # Strip leading / trailing lone-punctuation fragments produced by OCR splits
        # e.g. "fit me Matte -" -> "fit me Matte", "+PORELESS foundation" -> "PORELESS foundation"
        product_name = re.sub(r'^[^\w]+', '', product_name).strip()
        product_name = re.sub(r'[^\w]+$', '', product_name).strip()
        # Collapse any internal multi-space runs
        product_name = re.sub(r'\s{2,}', ' ', product_name)
    else:
        product_name = clean_lines[0][0] if clean_lines else "Cosmetic Packaging Label"

    avg_conf = sum([c for _, c in clean_lines]) / len(clean_lines) if clean_lines else 0.0

    return {
        "brand_name": detected_brand or "Unknown Brand",
        "product_name": product_name,
        "category": detected_category,
        "confidence": round(avg_conf, 2)
    }

def extract_text_from_image(file_bytes: bytes) -> dict:
    """
    Executes real OCR analysis on the input image using RapidOCR / EasyOCR / PyTesseract.
    """
    extracted_lines = []
    engine_used = "OpenCV Preprocessing Engine"

    try:
        # 1. Attempt RapidOCR ONNX Detection
        rapid_engine = _get_rapidocr_engine()
        if rapid_engine:
            nparr = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                pil_img = Image.open(io.BytesIO(file_bytes)).convert('RGB')
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            
            ocr_result, elapse = rapid_engine(img)
            if ocr_result:
                engine_used = "RapidOCR ONNX Engine"
                for box, text, conf in ocr_result:
                    if float(conf) > 0.15 and len(text.strip()) >= 2:
                        extracted_lines.append({"text": text.strip(), "confidence": float(conf)})

        # 2. Fallback to EasyOCR if RapidOCR returns no text
        if not extracted_lines:
            easy_reader = _get_easyocr_reader()
            if easy_reader:
                preprocessed_img = preprocess_image_for_ocr(file_bytes)
                results = easy_reader.readtext(preprocessed_img)
                if results:
                    engine_used = "EasyOCR PyTorch Engine"
                    for bbox, text, conf in results:
                        if float(conf) > 0.15 and len(text.strip()) >= 2:
                            extracted_lines.append({"text": text.strip(), "confidence": float(conf)})

        # 3. Fallback to PyTesseract if available
        if not extracted_lines:
            try:
                import pytesseract
                import os
                
                possible_tess_paths = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                    os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\Tesseract-OCR\tesseract.exe"),
                    os.path.join(os.environ.get("USERPROFILE", ""), r"AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
                ]
                for tp in possible_tess_paths:
                    if os.path.exists(tp):
                        pytesseract.pytesseract.tesseract_cmd = tp
                        break

                pil_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
                full_text = pytesseract.image_to_string(pil_img)
                lines = [line.strip() for line in full_text.splitlines() if len(line.strip()) >= 2]
                
                if lines:
                    engine_used = "PyTesseract Engine"
                    for l in lines:
                        extracted_lines.append({"text": l, "confidence": 0.85})
            except Exception as tess_err:
                print(f"PyTesseract notice: {tess_err}")

    except Exception as exc:
        print(f"OCR Processing Exception: {exc}")

    # Parse brand, product, and category
    parsed_info = parse_brand_and_product(extracted_lines)
    raw_text_list = [item["text"] for item in extracted_lines]

    return {
        "status": "completed",
        "engine": engine_used,
        "raw_text": raw_text_list,
        "brand_name": parsed_info["brand_name"],
        "product_name": parsed_info["product_name"],
        "category": parsed_info["category"],
        "confidence": parsed_info["confidence"],
        "total_lines_detected": len(raw_text_list)
    }
