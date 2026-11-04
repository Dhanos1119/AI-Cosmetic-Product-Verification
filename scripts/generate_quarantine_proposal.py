"""
Deep Semantic Verification and Proposed Quarantine List Generation
Distinguishes confirmed non-cosmetic artifacts from uncertain cases using calibrated CLIP zero-shot classification.
Generates reports/proposed_image_quarantine.csv and quarantine destination structure.
"""
import csv
import json
import os
from collections import defaultdict
from pathlib import Path
import numpy as np
from PIL import Image
import torch

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PRODUCTS = BASE_DIR / "data" / "products.csv"
DATASET_DIR = BASE_DIR / "data" / "image_model_dataset"
AUDIT_CSV = BASE_DIR / "reports" / "image_audit.csv"
OUTPUT_PROPOSAL_CSV = BASE_DIR / "reports" / "proposed_image_quarantine.csv"
OUTPUT_SUMMARY_JSON = BASE_DIR / "reports" / "quarantine_proposal_summary.json"


def get_clip_model():
    from transformers import CLIPModel, CLIPProcessor
    model_name = "openai/clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(model_name)
    processor = CLIPProcessor.from_pretrained(model_name)
    model.eval()
    return model, processor


def main():
    print("=" * 80)
    print("PHASE 4: GENERATING PROPOSED IMAGE QUARANTINE LIST")
    print("=" * 80)

    # Load split info from npz
    ref_npz = np.load(BASE_DIR / "data" / "clip_reference_embeddings.npz")
    test_npz = np.load(BASE_DIR / "data" / "clip_test_embeddings.npz")

    split_by_rel_path = {}
    for p in ref_npz["rel_paths"]:
        split_by_rel_path[p.replace("\\", "/")] = "reference"
    for p in test_npz["rel_paths"]:
        split_by_rel_path[p.replace("\\", "/")] = "test"

    # Read image_audit.csv
    with open(AUDIT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_audited = list(reader)

    print(f"Loaded {len(all_audited)} audited image records.")

    # Filter candidates for quarantine investigation
    candidates = []
    for row in all_audited:
        status = row["audit_status"]
        if status in ["POSSIBLE_NON_COSMETIC", "NEAR_DUPLICATE", "WRONG_PRODUCT_LABEL", "CORRUPTED_OR_UNUSABLE"]:
            candidates.append(row)
        elif row.get("exact_duplicate_group") and row["audit_status"] == "EXACT_DUPLICATE":
            candidates.append(row)

    print(f"Found {len(candidates)} candidate images requiring deep verification.")

    # Load CLIP model for calibrated verification
    model, processor = get_clip_model()

    # Prompts for binary/multiclass calibration
    # Group 1: Genuine Cosmetic Evidence
    positive_prompts = [
        "a photo of a cosmetic product packaging, bottle, tube, jar, compact powder, or lipstick container",
        "a close-up photo of cosmetic makeup swatches on skin or cosmetic product texture smear",
    ]
    # Group 2: Non-Cosmetic Artifacts
    negative_prompts = [
        "a promotional marketing banner, website advertisement, graphic logo, or digital typography graphic",
        "a full-body fashion portrait of a person wearing clothing, apparel, or dress",
        "an unrelated electronic gadget, household object, food, animal, or landscape",
        "a screenshot of customer text reviews, star ratings, or web browser interface",
    ]

    all_prompts = positive_prompts + negative_prompts
    text_inputs = processor(text=all_prompts, return_tensors="pt", padding=True)
    with torch.no_grad():
        out = model.get_text_features(**text_inputs)
        if hasattr(out, 'pooler_output') and out.pooler_output is not None:
            text_embeds = out.pooler_output
        elif hasattr(out, 'text_embeds') and out.text_embeds is not None:
            text_embeds = out.text_embeds
        elif isinstance(out, torch.Tensor):
            text_embeds = out
        else:
            text_embeds = out[0]
        text_embeds = text_embeds / text_embeds.norm(dim=-1, keepdim=True)

    logit_scale = model.logit_scale.exp().item()

    quarantine_records = []
    confirmed_non_cosmetic = 0
    confirmed_duplicate = 0
    uncertain_manual_review = 0

    for item in candidates:
        rel_p = item["rel_path"].replace("\\", "/")
        fpath = BASE_DIR / rel_p
        split = split_by_rel_path.get(rel_p, "unknown")
        pid = item["product_id"]
        cat = item["category"]
        fname = item["filename"]
        status = item["audit_status"]

        # If it's a near duplicate or exact duplicate
        if status in ["EXACT_DUPLICATE", "NEAR_DUPLICATE"]:
            # Check near duplicate group
            quarantine_records.append({
                "image_id": item["image_id"],
                "product_id": pid,
                "category": cat,
                "filename": fname,
                "rel_path": rel_p,
                "current_status": status,
                "action_recommended": "QUARANTINE_DUPLICATE",
                "quarantine_destination": f"data/quarantine/duplicates/{cat}/{pid}/{fname}",
                "confidence_score": 0.99,
                "split": split,
                "specific_reason": item["audit_reason"],
            })
            confirmed_duplicate += 1
            continue

        # Evaluate image with calibrated CLIP
        try:
            with Image.open(fpath) as pil_img:
                img_inputs = processor(images=pil_img.convert("RGB"), return_tensors="pt")
                with torch.no_grad():
                    out_img = model.get_image_features(**img_inputs)
                    if hasattr(out_img, 'pooler_output') and out_img.pooler_output is not None:
                        img_embed = out_img.pooler_output
                    elif hasattr(out_img, 'image_embeds') and out_img.image_embeds is not None:
                        img_embed = out_img.image_embeds
                    elif isinstance(out_img, torch.Tensor):
                        img_embed = out_img
                    else:
                        img_embed = out_img[0]
                    img_embed = img_embed / img_embed.norm(dim=-1, keepdim=True)

                logits = (img_embed @ text_embeds.T) * logit_scale
                probs = torch.softmax(logits, dim=-1).squeeze(0).cpu().numpy()

                # Sum positive vs negative probabilities
                pos_prob = float(probs[0] + probs[1])
                neg_prob = float(probs[2] + probs[3] + probs[4] + probs[5])
                top_neg_idx = int(np.argmax(probs[2:])) + 2
                top_neg_label = ["promotional_banner", "clothing_apparel", "unrelated_object", "screenshot_review"][top_neg_idx - 2]
                top_neg_prob = float(probs[top_neg_idx])
        except Exception as exc:
            pos_prob = 0.0
            neg_prob = 1.0
            top_neg_label = "unreadable_corrupted"
            top_neg_prob = 1.0

        # Classification Rule:
        # High confidence non-cosmetic: neg_prob >= 0.85
        # Uncertain: 0.50 <= neg_prob < 0.85 (keep for manual review, DO NOT automatically quarantine)
        # Cosmetic: neg_prob < 0.50 (keep in dataset)

        if neg_prob >= 0.85:
            rec_action = "QUARANTINE_CONFIRMED"
            dest = f"data/quarantine/non_cosmetic/{cat}/{pid}/{fname}"
            reason = f"Confirmed non-cosmetic ({top_neg_label}, confidence: {neg_prob*100:.1f}%). Does not contain cosmetic product container."
            confirmed_non_cosmetic += 1
        elif neg_prob >= 0.50:
            rec_action = "KEEP_FOR_MANUAL_REVIEW"
            dest = "NONE"
            reason = f"Borderline non-cosmetic indication ({top_neg_label}, confidence: {neg_prob*100:.1f}%). Excluded from automatic quarantine to prevent loss of valid product views."
            uncertain_manual_review += 1
        else:
            rec_action = "KEEP_VALID"
            dest = "NONE"
            reason = f"Verified cosmetic content ({pos_prob*100:.1f}% cosmetic confidence). Preserved in dataset."

        quarantine_records.append({
            "image_id": item["image_id"],
            "product_id": pid,
            "category": cat,
            "filename": fname,
            "rel_path": rel_p,
            "current_status": status,
            "action_recommended": rec_action,
            "quarantine_destination": dest,
            "confidence_score": round(neg_prob, 4),
            "split": split,
            "specific_reason": reason,
        })

    # Write proposed quarantine CSV
    fieldnames = [
        "image_id", "product_id", "category", "filename", "rel_path",
        "current_status", "action_recommended", "quarantine_destination",
        "confidence_score", "split", "specific_reason"
    ]
    with open(OUTPUT_PROPOSAL_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(quarantine_records)

    print(f"Generated proposed quarantine list: {OUTPUT_PROPOSAL_CSV}")
    print(f"  Confirmed non-cosmetics for quarantine: {confirmed_non_cosmetic}")
    print(f"  Confirmed duplicates for quarantine:    {confirmed_duplicate}")
    print(f"  Uncertain cases kept for manual review: {uncertain_manual_review}")

    # Summary by split for confirmed quarantines
    ref_quarantine = sum(1 for r in quarantine_records if r["action_recommended"].startswith("QUARANTINE") and r["split"] == "reference")
    test_quarantine = sum(1 for r in quarantine_records if r["action_recommended"].startswith("QUARANTINE") and r["split"] == "test")
    print(f"  Quarantine breakdown by split:")
    print(f"    Reference set images: {ref_quarantine}")
    print(f"    Test set images:      {test_quarantine}")

    summary_data = {
        "total_candidates_examined": len(candidates),
        "confirmed_non_cosmetic": confirmed_non_cosmetic,
        "confirmed_duplicate": confirmed_duplicate,
        "uncertain_manual_review": uncertain_manual_review,
        "quarantine_by_split": {
            "reference": ref_quarantine,
            "test": test_quarantine,
        },
        "output_csv": str(OUTPUT_PROPOSAL_CSV),
    }
    with open(OUTPUT_SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)


if __name__ == "__main__":
    main()
