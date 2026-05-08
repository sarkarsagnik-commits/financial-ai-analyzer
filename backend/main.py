from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.analysis import router as analysis_router
from routers.upload import router as upload_router
from config import settings
from utils.db import health_check as chroma_health

app = FastAPI(
    title="FinSight AI API",
    description="AI-powered financial document analysis for 10-K and 10-Q filings",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api/upload", tags=["Upload"])
app.include_router(analysis_router, prefix="/api/analysis", tags=["Analysis"])


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "FinSight AI"}


@app.get("/health/db", tags=["Health"])
def health_db():
    """Check ChromaDB connectivity and collection stats."""
    return chroma_health()