# CosmeticVerify — AI-Powered Cosmetic Product Verification & Marketplace Trust Engine

CosmeticVerify is an enterprise-grade, multi-modal artificial intelligence application designed to combat counterfeit cosmetic products, protect consumer health, and empower shoppers with transparent marketplace intelligence. By unifying state-of-the-art computer vision, optical character recognition (OCR), multi-platform live marketplace scraping, and natural language sentiment processing, CosmeticVerify validates product packaging authenticity, cross-references live listings on **Amazon**, **Daraz LK**, and **Temu**, and delivers an objective 5-factor trust recommendation.

---

## 🌟 Key Highlights & Capabilities

- **Zero-Shot Visual Identification (CLIP ViT-B/32)**: Extracts high-dimensional visual embeddings of product packaging and matches them against verified cosmetic product centroids, enhanced by a trained PyTorch residual adapter.
- **Optical Character Recognition & Semantic Parsing**: Leverages Tesseract OCR with fuzzy text matching to extract brand names, formulations, volume/weight markers, and shade labels directly from packaging imagery.
- **Automatic Non-Cosmetic Rejection**: Protects pipeline integrity by identifying and rejecting non-cosmetic imagery (food, electronics, household items) with diagnostic explanations before downstream processing.
- **Multi-Marketplace Price & Listing Intelligence**: Live scraping and validation across **Amazon**, **Daraz LK**, and **Temu** with real product titles, images, live local currencies (USD / LKR), seller credentials, and stock status—without fabricated mock data.
- **Platform-Specific Review Sentiment Analysis**: Deep NLP sentiment analysis performed independently per marketplace, breaking down customer feedback into positive/negative sentiment distributions, key theme highlights, and credibility indicators.
- **5-Factor Trust & Value Recommendation Engine**: Evaluates available listings using a weighted multi-criteria decision algorithm:
  - 🏷️ **Price Competitiveness (25%)**
  - ⭐ **Customer Rating Score (20%)**
  - 📦 **Review Volume & Statistical Power (15%)**
  - 💬 **Aspect Sentiment Health (20%)**
  - 🛡️ **Platform & Seller Credibility (20%)**
- **Modern Dark-Themed UI/UX**: Built with Next.js 16, Tailwind CSS, and custom brand tokens (`#0B0B12` dark background, `#191925` cards, purple `#A855F7` and pink `#EC4899` accents), featuring drag-and-drop uploads up to 15 MB and custom vector brand icons.
- **Configurable Demonstration Mode**: Supports rapid evaluation using offline fixtures (`1.png` Maybelline Foundation, `2.png` ColourPop Lipstick, and `3.png` Non-Cosmetic object) for predictable, deterministic demonstrations.

---

## 🏗️ System Architecture

CosmeticVerify employs a decoupled, three-tier microservice architecture designed for scalability, low latency, and modularity:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   CosmeticVerify Frontend (Client)                     │
│           Next.js 16 • React 19 • TypeScript • Tailwind CSS            │
│               Port 3000 — Dark UI, Uploader, Result Views               │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ Multipart Upload & Auth
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     API Gateway Backend (Node.js)                      │
│                  Express • Multer • CORS • File Check                  │
│                Port 5000 — Ingestion & Service Routing                 │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ Proxied Multipart & Data
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   AI & Computer Vision Engine (Python)                 │
│                 FastAPI • PyTorch • HuggingFace • Uvicorn              │
│                Port 8001 — Inference & Scraping Pipeline               │
│                                                                        │
│  ┌─────────────────────────┐             ┌──────────────────────────┐  │
│  │   CLIP ViT-B/32 Model   │             │   Tesseract OCR Engine   │  │
│  │   & Residual Adapter    │             │   Brand / Shade Matcher  │  │
│  └───────────┬─────────────┘             └────────────┬─────────────┘  │
│              │                                        │                │
│              ▼                                        ▼                │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │         Multi-Marketplace Scrapers (Amazon / Daraz / Temu)       │  │
│  └──────────────────────────────────┬───────────────────────────────┘  │
│                                     │                                  │
│              ┌──────────────────────┴───────────────────────┐          │
│              ▼                                              ▼          │
│  ┌────────────────────────┐                   ┌──────────────────────┐ │
│  │ NLP Sentiment Pipeline │                   │ 5-Factor Recommender │ │
│  └────────────────────────┘                   └──────────────────────┘ │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       Persistence & Data Layer                         │
│            PostgreSQL / SQLite • SQLAlchemy ORM • Alembic              │
│                 User Auth, Verification History, Scrapes               │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 💻 Technology Stack

| Tier | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | [Next.js 16](https://nextjs.org/) (App Router) | Server-side rendering, client hydration, and routing |
| | [React 19](https://react.dev/) & [TypeScript](https://www.typescriptlang.org/) | Type-safe reactive component tree |
| | [Tailwind CSS](https://tailwindcss.com/) & [Lucide Icons](https://lucide.dev/) | Dark theme design tokens, responsive layouts, iconography |
| **Backend Gateway** | [Node.js](https://nodejs.org/) & [Express](https://expressjs.com/) | REST API gateway, file validation, and proxying |
| | [Multer](https://github.com/expressjs/multer) | Secure streaming multipart upload handling (15 MB limit) |
| **AI & ML Engine** | [Python 3.11 / 3.13](https://www.python.org/) | High-performance machine learning runtime |
| | [FastAPI](https://fastapi.tiangolo.com/) & [Uvicorn](https://www.uvicorn.org/) | Asynchronous REST API serving predictions on port 8001 |
| | [PyTorch](https://pytorch.org/) & [HuggingFace Transformers](https://huggingface.co/) | OpenAI CLIP ViT-B/32 embeddings & residual adapter network |
| | [pytesseract](https://pypi.org/project/pytesseract/) | Optical character recognition for packaging typography |
| | [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) & [httpx](https://www.python-httpx.org/) | Real-time marketplace extraction and HTTP client |
| | [VADER](https://github.com/cjhutto/vaderSentiment) & [spaCy](https://spacy.io/) | Rule-based and statistical sentiment classification |
| **Database** | [PostgreSQL](https://www.postgresql.org/) / SQLite | Relational persistence for accounts, logs, and audits |
| | [SQLAlchemy](https://www.sqlalchemy.org/) & [Alembic](https://alembic.sqlalchemy.org/) | Python ORM and database migration versioning |

---

## 📁 Repository Directory Structure

```
AI-Cosmetic-Product-Verification/
├── frontend/                     # Next.js 16 TypeScript web application
│   ├── app/                      # App router pages, layouts, and brand icons
│   │   ├── favicon.ico           # Multi-resolution brand favicon
│   │   ├── icon.svg              # SVG brand icon with cosmetic & shield motifs
│   │   ├── layout.tsx            # Root layout with dark background and fonts
│   │   └── page.tsx              # Main verification dashboard & workflows
│   ├── components/               # Modular UI components
│   │   ├── Header.tsx            # Clean user greeting ("Hi, [Username]") and navigation
│   │   ├── Hero.tsx              # Application introduction banner
│   │   ├── ImageUploader.tsx     # Drag-and-drop file uploader (15 MB limit)
│   │   ├── VerificationResult.tsx # Product identity, visual confidence, and OCR cards
│   │   ├── VerificationWorkspace.tsx # Multi-step verification controller
│   │   ├── ReviewAnalysisModal.tsx  # Deep platform-specific review breakdown modal
│   │   ├── LoginModal.tsx        # Authentication modal for login
│   │   └── SignupModal.tsx       # Authentication modal for registration
│   ├── public/                   # Static assets and icons
│   └── package.json              # Frontend npm dependencies
│
├── backend/                      # Node.js Express API gateway
│   ├── src/
│   │   ├── controllers/          # Upload, auth, and marketplace proxy controllers
│   │   ├── middleware/           # File size/type validators and error handlers
│   │   ├── routes/               # Express routing tables
│   │   └── server.js             # Gateway entry point (Port 5000)
│   ├── data/
│   │   └── demo_products.json    # Demonstration dataset and simulated reviews
│   ├── uploads/                  # Temporary upload cache directory (.gitkeep)
│   ├── .env.example              # Environment variable template for backend
│   └── package.json              # Backend npm dependencies
│
├── ai-service/                   # Python FastAPI machine learning service
│   ├── app/
│   │   ├── routes/               # Analysis, authentication, and scraping endpoints
│   │   ├── schemas/              # Pydantic request/response validation models
│   │   ├── services/             # Core business & ML logic
│   │   │   ├── clip_service.py   # CLIP ViT-B/32 embedding extraction & matching
│   │   │   ├── ocr_service.py    # Packaging text extraction and normalization
│   │   │   ├── authenticity_service.py # Overall authenticity scoring logic
│   │   │   ├── sentiment_service.py    # Sentiment classification engine
│   │   │   ├── review_analysis_service.py # Platform-specific review analysis
│   │   │   ├── marketplace_comparison_service.py # 5-factor scoring engine
│   │   │   ├── demo_service.py   # Configurable demonstration fixture validator
│   │   │   └── scraping/         # Amazon, Daraz LK, and Temu scrapers
│   │   └── main.py               # FastAPI application entry point (Port 8001)
│   ├── requirements.txt          # Python dependency specifications
│   └── .env.example              # Environment variable template for AI service
│
├── data/                         # Datasets, precomputed embeddings, and centroids
│   ├── clip_centroids_cleaned.npy # Calibrated CLIP feature centroids
│   └── image_model_dataset/      # Reference image dataset organized by product ID
├── database/                     # SQLAlchemy models and connection manager
│   ├── models/                   # User, AnalysisLog, and Marketplace models
│   ├── connection.py             # Database engine and sessionmaker
│   └── alembic/                  # Database migration scripts
├── docs/                         # Technical documentation and audit reports
├── tests/                        # Comprehensive automated Pytest suite
│   ├── test_part2_demo_marketplace.py
│   ├── test_part3_reviews_recommendation.py
│   └── test_review_analysis.py
├── alembic.ini                   # Alembic migration configuration
├── .gitignore                    # Environment, artifact, and bytecode exclusions
└── README.md                     # Project documentation
```

---

## ⚙️ Prerequisites & Environment Setup

Ensure you have the following installed on your machine:
- **Node.js**: `v18.0.0` or higher (v20+ recommended)
- **Python**: `3.11` to `3.13`
- **Tesseract OCR**: Installed on your system path (e.g. `C:\Program Files\Tesseract-OCR\tesseract.exe` on Windows or `sudo apt install tesseract-ocr` on Ubuntu)
- **PostgreSQL** *(Optional for local SQLite fallback)*: PostgreSQL 14+

### Environment Configuration

Copy each `.env.example` file to create your local `.env`:

#### 1. AI Service (`ai-service/.env`)
```bash
cp ai-service/.env.example ai-service/.env
```
Key variables:
- `PORT=8001`
- `ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5000`
- `DATABASE_URL=postgresql+psycopg2://postgres:your_password@localhost:5432/cosmetic_verification_db` *(or SQLite fallback)*

#### 2. Backend Gateway (`backend/.env`)
```bash
cp backend/.env.example backend/.env
```
Key variables:
- `PORT=5000`
- `AI_SERVICE_URL=http://localhost:8001`
- `ALLOWED_ORIGINS=http://localhost:3000`

#### 3. Frontend Client (`frontend/.env.local`)
```bash
cp frontend/.env.example frontend/.env.local
```
Key variables:
- `NEXT_PUBLIC_BACKEND_URL=http://localhost:5000/api/upload`
- `NEXT_PUBLIC_LOGIN_URL=http://localhost:5000/api/auth/login`
- `NEXT_PUBLIC_SIGNUP_URL=http://localhost:5000/api/auth/signup`

---

## 🚀 Step-by-Step Installation & Startup

Follow the steps below to start all three services.

### Step 1: Start the AI Service (FastAPI — Port 8001)

```bash
# Navigate to the ai-service directory
cd ai-service

# Create and activate a Python virtual environment
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
# source venv/bin/activate

# Install required packages
pip install -r requirements.txt

# Start the FastAPI server using Uvicorn on Port 8001
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```
- **Health Check**: `http://localhost:8001/health`
- **Interactive Swagger Docs**: `http://localhost:8001/docs`

---

### Step 2: Start the Backend Gateway (Node.js Express — Port 5000)

```bash
# Open a new terminal and navigate to the backend directory
cd backend

# Install dependencies
npm install

# Start the development server
npm run dev
```
- **Gateway Health Check**: `http://localhost:5000/api/health`
- **Upload Endpoint**: `POST http://localhost:5000/api/upload`

---

### Step 3: Start the Frontend Application (Next.js — Port 3000)

```bash
# Open a new terminal and navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the Next.js development server
npm run dev
```
- **Web Application**: Access `http://localhost:3000` in your browser.

---

## 🗄️ Database Setup & Migrations

CosmeticVerify supports PostgreSQL for production and seamlessly falls back to a local SQLite database for rapid local development.

To initialize or apply database schema migrations via Alembic:

```bash
# From the project root with the Python virtual environment active:
alembic upgrade head
```

To create a new migration after modifying models in `database/models/`:
```bash
alembic revision --autogenerate -m "describe_schema_change"
alembic upgrade head
```

---

## 🧪 Testing & Quality Assurance

CosmeticVerify maintains automated test coverage across all layers.

### 1. AI Service & Marketplace Pytest Suite

Run the full automated backend test suite:

```bash
# Set offline mode for fast execution without redownloading HuggingFace weights
$env:HF_HUB_OFFLINE="1"  # PowerShell
# export HF_HUB_OFFLINE=1  # macOS/Linux

ai-service\venv\Scripts\python.exe -m pytest tests/test_part2_demo_marketplace.py tests/test_part3_reviews_recommendation.py tests/test_review_analysis.py -v
```

Expected result:
```
tests/test_part2_demo_marketplace.py::test_demo_mode_foundation_1_png PASSED
tests/test_part2_demo_marketplace.py::test_demo_mode_lipstick_2_png PASSED
tests/test_part2_demo_marketplace.py::test_demo_mode_non_cosmetic_3_png PASSED
tests/test_part3_reviews_recommendation.py::test_scenario_1_simulated_reviews_count PASSED
...
============================= 18 passed in 1.45s =============================
```

### 2. Frontend Type Checking

Verify strict TypeScript compliance with zero errors:

```bash
cd frontend
npx tsc --noEmit
```

### 3. Production Build Validation

Test that the Next.js frontend builds cleanly for production deployment:

```bash
cd frontend
npm run build
```

---

## 🔌 Core API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/upload` | Ingestion endpoint forwarding image files to AI analysis |
| `POST` | `/api/analyze` | AI multi-modal pipeline (CLIP + OCR + Non-Cosmetic check) |
| `GET` | `/api/marketplace/compare` | Multi-marketplace live search & comparison |
| `POST` | `/api/marketplace/scrape-url` | On-demand URL extraction and metadata parser |
| `GET` | `/api/reviews/analyze` | Platform-specific review analysis & sentiment breakdown |
| `POST` | `/api/auth/signup` | Secure user registration with hashed credentials |
| `POST` | `/api/auth/login` | User authentication returning session state |
| `GET` | `/health` | Service health status check |

---

## 🛡️ Trust & Ethical AI Guidelines

- **Real Data Priority**: CosmeticVerify prioritizes verified marketplace listings and never creates fictitious prices, ratings, or seller identities. If a marketplace blocks scraping or has no matching product, the system transparently indicates `Data Unavailable`.
- **Explainable Scores**: Authenticity and recommendation ratings include a factor-by-factor breakdown, ensuring consumers understand why a product or platform is rated as trustworthy or risky.
- **Privacy First**: Uploaded imagery is processed ephemerally in a secure temporary buffer and purged after inspection logs are committed.
