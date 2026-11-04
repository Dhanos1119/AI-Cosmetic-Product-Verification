# AI Cosmetic Product Verification & Marketplace Trust System

CosmeticVerify is an AI-powered system designed to verify cosmetic packaging authenticity, detect brand details, perform similarity matching, and recommend trustworthy marketplaces.

---

## 🏗️ Architecture

```
AI-Cosmetic-Product-Verification/
├── frontend/     # Next.js 16 + TypeScript UI (Port 3000)
├── backend/      # Node.js + Express + Multer Upload API (Port 5000)
└── ai-service/   # Python + FastAPI Image Inspection & ML Service (Port 8000)
```

---

## 🚀 How to Run

### 1. Start AI Service (FastAPI — Port 8000)
```bash
cd ai-service
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- Health Check: `http://localhost:8000/health`
- OpenAPI Docs: `http://localhost:8000/docs`

### 2. Start Backend Service (Express — Port 5000)
```bash
cd backend
npm install
npm run dev
```
- Health Check: `http://localhost:5000/api/health`
- Upload Endpoint: `POST http://localhost:5000/api/upload`

### 3. Start Frontend Service (Next.js — Port 3000)
```bash
cd frontend
npm install
npm run dev
```
- Web Application: `http://localhost:3000` (or `http://192.168.1.27:3000` on mobile)
