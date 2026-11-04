"""
Unit Test: OpenAI CLIP ViT-B/32 Image Embedding Projection, Shape, Dtype, and L2 Normalization Verification
"""

import sys
import io
from pathlib import Path
import numpy as np
import torch
from PIL import Image

BASE_DIR = Path(__file__).parent.parent.resolve()
AI_SERVICE_DIR = BASE_DIR / "ai-service"

if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.services.clip_service import _get_clip_model_and_processor, extract_image_embedding

def test_clip_embedding_tensor_properties():
    print("=" * 70)
    print("OPENAI CLIP ViT-B/32 EMBEDDING TENSOR PROPERTIES AUDIT")
    print("=" * 70)

    model, processor = _get_clip_model_and_processor()
    pil_img = Image.new("RGB", (224, 224), color="blue")
    inputs = processor(images=pil_img, return_tensors="pt")

    with torch.no_grad():
        # 1. Unprojected Vision Transformer Output (768-dim)
        vision_out = model.vision_model(**inputs)
        unprojected_tensor = vision_out.pooler_output  # shape: (1, 768)

        # 2. Projected Joint Multimodal Output (512-dim) via visual_projection
        projected_tensor = model.visual_projection(unprojected_tensor)  # shape: (1, 512)

        # 3. get_image_features output
        get_out = model.get_image_features(**inputs)
        get_tensor = get_out.pooler_output if hasattr(get_out, "pooler_output") else get_out

        # L2 norm before normalization
        l2_norm_before = float(projected_tensor.norm(p=2, dim=-1))

        # L2 norm after normalization
        norm_tensor = projected_tensor / projected_tensor.norm(p=2, dim=-1, keepdim=True)
        l2_norm_after = float(norm_tensor.norm(p=2, dim=-1))

    # Verify tensor equivalence
    assert torch.allclose(projected_tensor, get_tensor, atol=1e-6), "get_image_features output must match visual_projection"
    assert unprojected_tensor.shape == (1, 768), f"Expected unprojected shape (1, 768), got {unprojected_tensor.shape}"
    assert projected_tensor.shape == (1, 512), f"Expected projected shape (1, 512), got {projected_tensor.shape}"

    # Verify extract_image_embedding output (numpy 1D array)
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG")
    file_bytes = buf.getvalue()

    final_vec = extract_image_embedding(file_bytes)

    print(f"1. Tensor Type (PyTorch):         {type(projected_tensor)}")
    print(f"2. Unprojected Tensor Shape:      {unprojected_tensor.shape} (768-dim Vision Backbone)")
    print(f"3. Projected Tensor Shape:        {projected_tensor.shape} (512-dim Joint Multimodal Space)")
    print(f"4. Tensor Dtype:                  {projected_tensor.dtype}")
    print(f"5. L2 Norm Before Normalization:  {l2_norm_before:.6f}")
    print(f"6. L2 Norm After Normalization:   {l2_norm_after:.6f}")
    print(f"7. Final Vector Type (NumPy):     {type(final_vec)}")
    print(f"8. Final Vector Shape:            {final_vec.shape}")
    print(f"9. Final Vector Dtype:            {final_vec.dtype}")
    print(f"10. Final Vector L2 Norm:         {float(np.linalg.norm(final_vec)):.6f}")

    assert isinstance(final_vec, np.ndarray), "Final embedding must be a numpy ndarray"
    assert final_vec.shape == (512,), f"Final vector shape must be (512,), got {final_vec.shape}"
    assert final_vec.dtype == np.float32, f"Final vector dtype must be float32, got {final_vec.dtype}"
    assert np.isclose(np.linalg.norm(final_vec), 1.0, atol=1e-4), f"Final vector L2 norm must be ~1.0, got {np.linalg.norm(final_vec)}"

    print("=" * 70)
    print("ALL EMBEDDING TENSOR PROPERTY AUDITS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    test_clip_embedding_tensor_properties()
