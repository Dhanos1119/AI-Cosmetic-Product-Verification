"""
Data Preparation Script: 100,000 Cosmetic Product Review Dataset
Generates and indexes 100,000 domain-specific cosmetic product reviews mapped across
the 30 catalog products (P001 - P030) and 5 categories (Lip_Products, Foundation_Base, Eye_Products, Skin_Care, Other_Makeup).

Dataset Schema:
- review_id (str): Unique review identifier
- product_id (str): Associated catalog product ID (P001 - P030)
- brand (str): Brand name
- product_name (str): Product title
- category (str): Product category
- author (str): Review author name
- rating (float): Star rating (1.0 - 5.0)
- review_headline (str): Short summary title
- review_body (str): Full review comment text
- verified_purchase (bool): Verified buyer badge
- vine (bool): Incentivized / promotional review flag
- label (str): 'OR' (Original/Genuine), 'CG' (Computer-Generated/Fake), 'INCENTIVIZED' (Promotional)
- review_date (str): ISO date
"""

import os
import sys
import json
import random
import gzip
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DATA_DIR = Path(__file__).parent.resolve()
DATASET_JSONL_GZ = DATA_DIR / "reviews_100k_dataset.jsonl.gz"
DATASET_SQLITE = DATA_DIR / "reviews_100k.db"

CATALOG_PRODUCTS = [
    # Lip_Products
    {"product_id": "P001", "brand": "Colourpop", "product_name": "Lippie Pencil", "category": "Lip_Products"},
    {"product_id": "P002", "brand": "Sally B's Skin Yummies", "product_name": "B_Glossy Lip Gloss", "category": "Lip_Products"},
    {"product_id": "P003", "brand": "Penny Lane Organics", "product_name": "Lip Gloss", "category": "Lip_Products"},
    {"product_id": "P004", "brand": "Nudus", "product_name": "Amalia", "category": "Lip_Products"},
    {"product_id": "P005", "brand": "Marienatie", "product_name": "Lipstick", "category": "Lip_Products"},
    {"product_id": "P006", "brand": "Coastal Classic Creation", "product_name": "Conch Lipstick", "category": "Lip_Products"},

    # Foundation_Base
    {"product_id": "P007", "brand": "Deciem", "product_name": "Coverage Foundation", "category": "Foundation_Base"},
    {"product_id": "P008", "brand": "w3llpeople", "product_name": "Realist Invisible Setting Powder", "category": "Foundation_Base"},
    {"product_id": "P009", "brand": "rejuva minerals", "product_name": "Pressed Powder Foundation", "category": "Foundation_Base"},
    {"product_id": "P010", "brand": "glossier", "product_name": "Stretch Concealer", "category": "Foundation_Base"},
    {"product_id": "P011", "brand": "fenty", "product_name": "MATCH STIX - Matte Skinstick", "category": "Foundation_Base"},
    {"product_id": "P012", "brand": "Clinique", "product_name": "Even Better Compact Makeup Broad Spectrum SPF 15", "category": "Foundation_Base"},
    {"product_id": "P019", "brand": "Iman", "product_name": "CC Correct Cover Clay Medium Deep", "category": "Foundation_Base"},
    {"product_id": "P020", "brand": "Smashbox", "product_name": "24 Hour CC Spot Concealer", "category": "Foundation_Base"},
    {"product_id": "P023", "brand": "Marcelle", "product_name": "BB Cream To Powder Makeup", "category": "Foundation_Base"},
    {"product_id": "P024", "brand": "Cargo Cosmetics", "product_name": "Onebase For Face", "category": "Foundation_Base"},

    # Eye_Products
    {"product_id": "P013", "brand": "zorah biocosmetiques", "product_name": "Liquid Liner", "category": "Eye_Products"},
    {"product_id": "P014", "brand": "maia's mineral galaxy", "product_name": "Mineral Eye Brow Liner Charcoal Brown", "category": "Eye_Products"},
    {"product_id": "P015", "brand": "lotus cosmetics usa", "product_name": "Mascara", "category": "Eye_Products"},
    {"product_id": "P016", "brand": "green people", "product_name": "Volumising Mascara", "category": "Eye_Products"},
    {"product_id": "P017", "brand": "c'est moi", "product_name": "Muse Mascara", "category": "Eye_Products"},
    {"product_id": "P018", "brand": "alva", "product_name": "Liquid Eye Shadow", "category": "Eye_Products"},

    # Other_Makeup
    {"product_id": "P021", "brand": "dr. hauschka", "product_name": "Dr. Hauschka Translucent Bronzing Tint", "category": "Other_Makeup"},
    {"product_id": "P022", "brand": "physicians formula", "product_name": "Physicians Formula Bronze Booster Glow-Boosting BB Cream", "category": "Other_Makeup"},
    {"product_id": "P025", "brand": "dior", "product_name": "Junon", "category": "Other_Makeup"},
    {"product_id": "P026", "brand": "benefit", "product_name": "dallas dusty rose face powder", "category": "Other_Makeup"},
    {"product_id": "P027", "brand": "stila", "product_name": "Stila Stay All Day Bronzer in Medium", "category": "Other_Makeup"},
    {"product_id": "P028", "brand": "mineral fusion", "product_name": "Mineral Fusion Bronzer Duo", "category": "Other_Makeup"},
    {"product_id": "P029", "brand": "nyx", "product_name": "NYX Mosaic Powder Blush Paradise", "category": "Other_Makeup"},
    {"product_id": "P030", "brand": "annabelle", "product_name": "Annabelle Biggy Bronzer Haute Gold", "category": "Other_Makeup"},
]

GENUINE_HEADLINES_POSITIVE = [
    "Holy grail product!", "Absolutely love this!", "Great formula and finish",
    "Exceeded my expectations", "Definite repurchase", "Best I have tried in years",
    "Smooth application", "Stays all day", "Perfect shade match", "Will buy again!"
]

GENUINE_TEXTS_POSITIVE = [
    "This formula is amazing. It applies smoothly, doesn't crease, and lasts throughout the entire day. Highly recommend for daily wear.",
    "I was skeptical at first, but this exceeded my expectations. The pigment is rich, it feels lightweight on the skin, and it doesn't cause breakouts.",
    "Beautiful texture and shade payoff! Looks natural under daylight and holds up well even in humid weather.",
    "Hands down the best cosmetic purchase I've made this year. Glides on easily, stays vibrant for hours, and blends seamlessly.",
    "Super impressed with the quality. The packaging is sleek and the product itself delivers fantastic results without drying out skin."
]

GENUINE_HEADLINES_NEGATIVE = [
    "Not worth the hype", "Formula was disappointing", "Did not work for me",
    "Caused dry patches", "Color was completely off", "Poor longevity"
]

GENUINE_TEXTS_NEGATIVE = [
    "I really wanted to love this, but the formula felt heavy and settled into fine lines after just two hours of wear.",
    "The color in person is much different than shown online. It felt patchy during application and wore off quickly.",
    "Caused irritation on my skin within a day of use. Not suitable for sensitive skin types unfortunately.",
    "Very disappointing coverage. Was very sheer and required multiple layers, which ended up looking cakey."
]

FAKE_CG_HEADLINES = [
    "BEST PRODUCT EVER!!!!! MUST BUY NOW!!!!!", "AMAZING VUE GREAT SHADE PERFECT",
    "Top quality item fast shipping highly recommend 100%", "BUY THIS RIGHT NOW BEST PRODUCT ON EARTH",
    "Super good product very cheap fast delivery seller good"
]

FAKE_CG_TEXTS = [
    "BEST PRODUCT EVER!!!!! BUY THIS RIGHT NOW!!!!! AMAZING QUALITY SO GOOD WOW FAST SHIPPING PERFECT!!!!! 10/10!!!!!",
    "Great product great quality great seller fast shipping item as described very good product buy again soon 100% recommended!",
    "Amazing product works very good highly recommended top quality best price fast delivery 5 stars seller is very good!",
    "Super good product super fast shipping best quality item very nice I love it so much buy now right now 100% good!",
    "Product is super super super good fast delivery seller very nice best price top quality buy buy buy!"
]

INCENTIVIZED_HEADLINES = [
    "Received for honest review", "Vine Customer Review of Free Product",
    "Promotional Product Review", "Complimentary sample testing"
]

INCENTIVIZED_TEXTS = [
    "I received this product for free in exchange for an honest review. Overall, it performs nicely, leaves a nice finish, and has pleasant packaging.",
    "Discounted product provided for evaluation purposes. The texture is smooth and easy to apply, though longevity is average.",
    "Complimentary sample received from brand. Applies smoothly, gives a nice glow, and looks good for daily wear."
]

FIRST_NAMES = ["Jessica", "Ashley", "Emily", "Sarah", "Amanda", "Samantha", "Rachel", "Megan", "Hannah", "Brittany", "Taylor", "Lauren", "Kayla", "Alexis", "Victoria", "Elizabeth", "Chloe", "Olivia", "Sophia", "Ava", "Emma", "Isabella", "Mia", "Abigail", "Grace", "Zoey", "Riley", "Lily", "Harper", "Evelyn"]
LAST_INITIALS = ["A.", "B.", "C.", "D.", "E.", "F.", "G.", "H.", "K.", "M.", "N.", "P.", "R.", "S.", "T.", "W."]

def generate_reviews(target_count: int = 100000):
    print(f"Generating {target_count:,} cosmetic product review dataset...")
    reviews = []
    start_date = datetime(2025, 1, 1)

    for i in range(target_count):
        product = random.choice(CATALOG_PRODUCTS)
        review_id = f"REV_{i+1:06d}"
        author = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_INITIALS)}"
        rand_date = start_date + timedelta(days=random.randint(0, 450), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        date_str = rand_date.strftime("%Y-%m-%d")

        # Roll review label: 70% Genuine ('OR'), 20% Computer-Generated Fake ('CG'), 10% Incentivized ('INCENTIVIZED')
        roll = random.random()
        if roll < 0.70:
            label = "OR"
            is_verified = random.random() < 0.88  # 88% verified for genuine
            is_vine = False

            if random.random() < 0.85:
                rating = round(random.uniform(4.0, 5.0), 1)
                headline = random.choice(GENUINE_HEADLINES_POSITIVE)
                body = random.choice(GENUINE_TEXTS_POSITIVE)
            else:
                rating = round(random.uniform(1.0, 3.0), 1)
                headline = random.choice(GENUINE_HEADLINES_NEGATIVE)
                body = random.choice(GENUINE_TEXTS_NEGATIVE)

        elif roll < 0.90:
            label = "CG"
            is_verified = random.random() < 0.15  # Only 15% verified for fake/CG
            is_vine = False
            rating = 5.0 if random.random() < 0.90 else 1.0
            headline = random.choice(FAKE_CG_HEADLINES)
            body = random.choice(FAKE_CG_TEXTS)

        else:
            label = "INCENTIVIZED"
            is_verified = False
            is_vine = True
            rating = round(random.uniform(4.0, 5.0), 1)
            headline = random.choice(INCENTIVIZED_HEADLINES)
            body = random.choice(INCENTIVIZED_TEXTS)

        rev_item = {
            "review_id": review_id,
            "product_id": product["product_id"],
            "brand": product["brand"],
            "product_name": product["product_name"],
            "category": product["category"],
            "author": author,
            "rating": rating,
            "review_headline": headline,
            "review_body": body,
            "verified_purchase": is_verified,
            "vine": is_vine,
            "label": label,
            "review_date": date_str
        }
        reviews.append(rev_item)

        if (i + 1) % 25000 == 0:
            print(f"  Generated {i+1:,} / {target_count:,} reviews...")

    return reviews


def save_dataset(reviews):
    print(f"\nSaving dataset to gzip JSONL: {DATASET_JSONL_GZ}")
    with gzip.open(DATASET_JSONL_GZ, "wt", encoding="utf-8") as gz:
        for r in reviews:
            gz.write(json.dumps(r) + "\n")

    print(f"Indexing dataset into SQLite database: {DATASET_SQLITE}")
    if DATASET_SQLITE.exists():
        os.remove(DATASET_SQLITE)

    conn = sqlite3.connect(DATASET_SQLITE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE reviews (
            review_id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            brand TEXT NOT NULL,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            author TEXT,
            rating REAL,
            review_headline TEXT,
            review_body TEXT,
            verified_purchase INTEGER,
            vine INTEGER,
            label TEXT,
            review_date TEXT
        );
    """)

    cursor.execute("CREATE INDEX idx_reviews_product_id ON reviews(product_id);")
    cursor.execute("CREATE INDEX idx_reviews_brand ON reviews(brand);")
    cursor.execute("CREATE INDEX idx_reviews_label ON reviews(label);")
    cursor.execute("CREATE INDEX idx_reviews_category ON reviews(category);")

    cursor.executemany("""
        INSERT INTO reviews (
            review_id, product_id, brand, product_name, category, author,
            rating, review_headline, review_body, verified_purchase, vine, label, review_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, [
        (
            r["review_id"], r["product_id"], r["brand"], r["product_name"], r["category"], r["author"],
            r["rating"], r["review_headline"], r["review_body"], 1 if r["verified_purchase"] else 0,
            1 if r["vine"] else 0, r["label"], r["review_date"]
        )
        for r in reviews
    ])

    conn.commit()
    conn.close()

    gz_size = DATASET_JSONL_GZ.stat().st_size / (1024 * 1024)
    db_size = DATASET_SQLITE.stat().st_size / (1024 * 1024)
    print(f"Dataset successfully created and indexed!")
    print(f"  Gzip JSONL file size: {gz_size:.2f} MB")
    print(f"  SQLite DB file size  : {db_size:.2f} MB")


if __name__ == "__main__":
    revs = generate_reviews(100000)
    save_dataset(revs)
