# Financial AI Analyzer (FinSight AI)

## Overview

FinSight AI is an end-to-end system that extracts structured insights from SEC filings (10-K / 10-Q). It combines **deterministic financial analysis** (regex, keyword scoring) with **LLM-based interpretation** (OpenAI GPT) using a modular backend architecture powered by FastAPI, ChromaDB, and LangChain.

---

## Features

### 1. Financial Changes (What Changed)
- Extracts revenue, EPS, net income, total assets, and 5+ other metrics
- Computes year-over-year percentage changes
- **AI-generated explanation** of key financial movements (requires OpenAI API key)

### 2. Risk Radar
- Identifies risks across 9 categories (Market, Regulatory, Cyber, ESG, etc.)
- Scores severity as High / Medium / Low using keyword taxonomy
- **AI-generated executive risk summary**

### 3. Management Outlook
- Classifies management tone (Positive → Negative scale)
- Extracts forward-looking guidance statements
- **AI-generated sentiment interpretation**

### 4. RAG Q&A
- Upload a PDF → LangChain chunks it → OpenAI embeds into FAISS
- Ask natural language questions → retrieves relevant context → GPT answers
- Full retrieval-augmented generation pipeline

### 5. Semantic Search
- ChromaDB-powered vector search over uploaded documents
- Returns relevant chunks ranked by similarity score

### 6. Authentication
- JWT-based login and registration
- Protected API endpoints with Bearer token

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, Uvicorn, Pydantic |
| **AI / LLM** | OpenAI GPT-4o-mini, LangChain |
| **Vector DB** | ChromaDB (semantic search), FAISS (RAG) |
| **Embeddings** | OpenAI text-embedding-3-small, sentence-transformers (local) |
| **PDF Parsing** | pypdf |
| **Frontend** | Streamlit |
| **Auth** | python-jose (JWT), hashlib (password hashing) |

---

## Project Structure

```
financial-ai-analyzer/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Pydantic Settings (env vars)
│   ├── .env.example               # Required env vars template
│   ├── routers/
│   │   ├── analysis.py            # Auth, analysis, RAG, document endpoints
│   │   └── upload.py              # File upload endpoint
│   ├── services/
│   │   ├── analysis_service.py    # 3 analysis modules + RAG pipeline + LLM enrichment
│   │   └── file_service.py        # PDF save/delete/lookup
│   ├── models/
│   │   ├── request_models.py      # Pydantic request schemas
│   │   └── response_models.py     # Pydantic response schemas
│   ├── utils/
│   │   ├── db.py                  # ChromaDB manager (singleton)
│   │   ├── jwt_handler.py         # JWT create/decode/verify
│   │   └── auth_utils.py          # User registration & authentication
│   └── data/                      # Sample PDFs (gitignored)
│
├── frontend/
│   ├── app.py                     # Streamlit entry point
│   ├── config.py                  # API base URL config
│   ├── styles.css                 # Dark theme CSS
│   ├── pages/
│   │   ├── login.py               # Login / Register page
│   │   └── dashboard.py           # Upload, analysis, results, search
│   └── utils/
│       ├── auth.py                # Frontend auth wrapper
│       ├── jwt_handler.py         # Token storage + API calls
│       └── ui.py                  # Styled cards and components
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Setup Instructions

### 1. Clone and Setup

```bash
git clone https://github.com/sarkarsagnik-commits/financial-ai-analyzer.git
cd financial-ai-analyzer
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

### 2. Configure Environment (Optional — for LLM features)

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and add your OPENAI_API_KEY
```

> **Without API key**: All analysis modules, upload, search, and auth work.
> The AI explanations will show "unavailable" and RAG Q&A returns an error.

### 3. Run Backend

```bash
cd backend
python -m uvicorn main:app --reload
```

Open API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Run Frontend

```bash
cd frontend
streamlit run app.py
```

Open: [http://localhost:8501](http://localhost:8501)

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/analysis/auth/login` | ❌ | JWT login |
| `POST` | `/api/analysis/auth/register` | ❌ | Create account |
| `POST` | `/api/upload/` | 🔒 | Upload PDF → extract → chunk → index |
| `POST` | `/api/analysis/run` | 🔒 | Run analysis modules |
| `POST` | `/api/analysis/query` | 🔒 | Semantic search over document |
| `POST` | `/api/analysis/rag` | 🔒 | RAG-powered Q&A (needs API key) |
| `GET`  | `/api/analysis/documents` | 🔒 | List all documents |
| `GET`  | `/api/analysis/documents/{id}` | 🔒 | Document info + chunk count |
| `DELETE` | `/api/analysis/documents/{id}` | 🔒 | Delete document |
| `GET`  | `/health` | ❌ | Service health check |
| `GET`  | `/health/db` | ❌ | ChromaDB health + stats |

---

## Development Workflow

- `main` → stable/production branch
- `dev` → integration branch (all features)
- `dev2` → archive (consolidated work)
- `feature/*` → individual feature branches

---

## Team Structure

- Backend & RAG
- PDF Parsing
- Financial Metrics
- LLM Prompt Engineering
- Frontend
- Authentication & Integration

---

## Notes

- LLM does **not** compute financial metrics — deterministic logic handles numerical analysis
- RAG is used for contextual interpretation and Q&A
- All features degrade gracefully without an API key

---

## License

This project is for academic and learning purposes.
