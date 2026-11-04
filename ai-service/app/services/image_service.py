import io
import numpy as np
import cv2
from PIL import Image

ALLOWED_FORMATS = {"JPEG", "JPG", "PNG", "WEBP"}

def resize_image_if_needed(file_bytes: bytes, max_dim: int = 1600) -> bytes:
    """
    Safely resizes oversized images down to max_dim (preserving aspect ratio)
    to prevent memory spikes, excessive OCR latency, and repeated slow inference.
    """
    try:
        pil_img = Image.open(io.BytesIO(file_bytes))
        width, height = pil_img.size
        if max(width, height) <= max_dim:
            return file_bytes

        scale = max_dim / float(max(width, height))
        new_w = max(1, int(width * scale))
        new_h = max(1, int(height * scale))

        if pil_img.mode in ("RGBA", "LA") or (pil_img.mode == "P" and "transparency" in pil_img.info):
            resized = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            out_buf = io.BytesIO()
            resized.save(out_buf, format="PNG", optimize=True)
            return out_buf.getvalue()
        else:
            resized = pil_img.convert("RGB").resize((new_w, new_h), Image.Resampling.LANCZOS)
            out_buf = io.BytesIO()
            resized.save(out_buf, format="JPEG", quality=92, optimize=True)
            return out_buf.getvalue()
    except Exception:
        return file_bytes

def validate_and_inspect_image(file_bytes: bytes, filename: str) -> dict:
    """
    Validates uploaded image bytes using Pillow & OpenCV and returns image dimensions and metadata.
    Raises ValueError on empty, invalid, or corrupted images.
    """
    if not file_bytes or len(file_bytes) == 0:
        raise ValueError("Uploaded file is empty (0 bytes).")

    # Read image using Pillow
    try:
        pil_img = Image.open(io.BytesIO(file_bytes))
        pil_img.verify()  # Verify image integrity
        
        # Re-open after verify() as PIL requires
        pil_img = Image.open(io.BytesIO(file_bytes))
        width, height = pil_img.size
        img_format = (pil_img.format or "UNKNOWN").upper()
    except Exception as e:
        raise ValueError(f"Corrupted or invalid image file. Details: {str(e)}")

    # Check allowed formats
    if img_format not in ALLOWED_FORMATS:
        # Check filename extension as fallback
        ext = filename.split(".")[-1].upper() if "." in filename else ""
        if ext in {"JPG", "JPEG"}:
            img_format = "JPEG"
        elif ext == "PNG":
            img_format = "PNG"
        elif ext == "WEBP":
            img_format = "WEBP"
        else:
            raise ValueError(f"Unsupported image format '{img_format}'. Only JPG, JPEG, PNG, and WEBP files are allowed.")

    # Decode image using OpenCV to ensure NumPy matrix compatibility
    nparr = np.frombuffer(file_bytes, np.uint8)
    cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if cv_img is None:
        raise ValueError("Failed to decode image with OpenCV. File may be corrupted or incomplete.")

    cv_height, cv_width, _ = cv_img.shape

    return {
        "filename": filename,
        "image_validation": "valid",
        "width": width or cv_width,
        "height": height or cv_height,
        "format": img_format,
        "size": len(file_bytes)
    }
