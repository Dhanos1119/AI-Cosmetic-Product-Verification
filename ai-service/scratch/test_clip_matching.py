import os, csv
from pathlib import Path
import numpy as np
import cv2

base_dir = r'C:\Users\Dhanoshigan Ratnaraj\AI-Cosmetic-Product-Verification\data'
dataset_dir = os.path.join(base_dir, 'image_model_dataset')
csv_products = os.path.join(base_dir, 'selected_30_products_final.csv')

def extract_feat(img_path):
    img = cv2.imread(img_path)
    if img is None:
        return None
    resized = cv2.resize(img, (224, 224), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
    h_hist = cv2.calcHist([hsv], [0], None, [128], [0, 180]).flatten()
    s_hist = cv2.calcHist([hsv], [1], None, [128], [0, 256]).flatten()
    v_hist = cv2.calcHist([hsv], [2], None, [128], [0, 256]).flatten()
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    mag = cv2.magnitude(sobelx, sobely)
    mag_hist = cv2.calcHist([mag.astype(np.float32)], [0], None, [128], [0, 256]).flatten()
    vec = np.concatenate([h_hist, s_hist, v_hist, mag_hist])
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec

product_catalog = {}
with open(csv_products, mode='r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        pid = row['product_id'].strip()
        product_catalog[pid] = {
            'product_id': pid,
            'brand': row['brand'].strip(),
            'product_name': row['product_name'].strip(),
            'category': row['category'].strip(),
            'product_type': row['product_type'].strip(),
        }

pids = []
centroids = []

for cat in sorted(os.listdir(dataset_dir)):
    cat_path = os.path.join(dataset_dir, cat)
    if not os.path.isdir(cat_path):
        continue
    for pfolder in sorted(os.listdir(cat_path)):
        pf_path = os.path.join(cat_path, pfolder)
        if not os.path.isdir(pf_path):
            continue
        pid = pfolder.split('_')[0]
        imgs = [os.path.join(pf_path, f) for f in os.listdir(pf_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        sample_imgs = imgs[:10]
        vecs = [extract_feat(p) for p in sample_imgs if extract_feat(p) is not None]
        if vecs:
            avg_vec = np.mean(vecs, axis=0)
            avg_vec = avg_vec / np.linalg.norm(avg_vec)
            pids.append(pid)
            centroids.append(avg_vec)
            product_catalog[pid]['folder_name'] = pfolder

centroids_mat = np.array(centroids)

# Test query image from P001 Colourpop Lippie Pencil
test_img = os.path.join(dataset_dir, 'Lip_Products', 'P001_Colourpop_LippiePencil', 'P001_0001.jpg')
query_vec = extract_feat(test_img)

sims = np.dot(centroids_mat, query_vec)

top_indices = np.argsort(sims)[::-1][:5]

print('=== TOP 5 PRODUCT MATCHES FOR P001_0001.jpg ===')
for rank, idx in enumerate(top_indices, start=1):
    pid = pids[idx]
    info = product_catalog[pid]
    raw_sim = float(sims[idx])
    pct = round(raw_sim * 100, 1)
    print(f"Rank #{rank}: Product {pid} | Brand: {info['brand']} | Name: {info['product_name']} | Category: {info['category']} ({pct}% similarity)")
