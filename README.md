# Financial AI Analyzer

## Overview

Financial AI Analyzer is an end-to-end system that extracts structured insights from SEC filings (10-K / 10-Q).
It combines deterministic financial analysis with LLM-based interpretation using a modular backend architecture.

---

## Core Features

### 1. Financial Changes (What Changed)

* Revenue growth
* EPS growth
* Net margin
* Debt-to-equity
* Free cash flow
* AI-generated explanation of financial movement

---

### 2. Risk Radar

* Extracts Risk Factors section
* Uses retrieval-based analysis (RAG)
* Summarizes top risk themes
* Provides structured insights

---

### 3. Management Outlook

* Extracts MD&A section
* Classifies tone (Positive / Neutral / Cautious)
* Identifies forward-looking statements

---

## Tech Stack

### Backend

* FastAPI
* Python 3.13
* Pydantic
* Uvicorn

### AI / Data (Planned)

* OpenAI API
* ChromaDB (Vector DB)
* LangChain (optional)

### Data Processing

* pdfplumber
* pandas
* numpy

### Frontend

* Streamlit

### Auth & Storage

* SQLite
* bcrypt

---

## Project Structure

```
financial-ai-analyzer/
│
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── routers/
│   ├── services/
│   ├── models/
│   ├── rag/
│   ├── utils/
│   └── data/
│
├── frontend/
│   └── streamlit_app.py
│
├── database/
├── tests/
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### 1. Clone Repository

```
git clone https://github.com/<your-username>/financial-ai-analyzer.git
cd financial-ai-analyzer
```

---

### 2. Create Virtual Environment

Windows:

```
python -m venv venv
venv\Scripts\activate
```

---

### 3. Install Dependencies

```
pip install -r requirements.txt
```

---

### 4. Run Backend

```
uvicorn backend.main:app --reload
```

Open:

```
http://127.0.0.1:8000/docs
```

---

### 5. Run Frontend

```
streamlit run frontend/streamlit_app.py
```

---

## API Endpoints (Phase 1)

### Health Check

```
GET /health
```

---

### Upload File

```
POST /upload
```

---

### Run Analysis

```
POST /run-analysis
```

---

## Development Workflow

* `main` → stable branch
* `dev` → integration branch
* feature branches → development

Example:

```
feature/backend-skeleton
feature/rag-engine
feature/frontend-ui
```

---

## Current Status

Phase 1 (In Progress):

* Backend skeleton
* File upload
* API structure

Upcoming:

* PDF parsing
* Metrics engine
* RAG integration
* LLM analysis

---

## Team Structure

* Backend & RAG
* PDF Parsing
* Financial Metrics
* LLM Prompt Engineering
* Frontend
* Authentication & Integration

---

## Notes

* LLM does not compute financial metrics
* Deterministic logic used for numerical analysis
* RAG used for contextual interpretation

---

## License

This project is for academic and learning purposes.
