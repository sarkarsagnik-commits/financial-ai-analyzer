from fastapi import APIRouter, Depends, HTTPException
from models.request_models import AnalysisRequest, LoginRequest, RegisterRequest, QueryRequest
from models.response_models import AnalysisResponse, TokenResponse
from services.analysis_service import run_analysis, query_document
from utils.jwt_handler import get_current_user, create_access_token
from utils.auth_utils import authenticate_user, create_user
from config import settings

router = APIRouter()


# ── Auth endpoints ─────────────────────────────────────────────────────────

@router.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
def login(payload: LoginRequest):
    user = authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"sub": user["id"], "email": user["email"]})
    return TokenResponse(access_token=token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)


@router.post("/auth/register", response_model=TokenResponse, tags=["Auth"])
def register(payload: RegisterRequest):
    try:
        user = create_user(payload.email, payload.password, payload.full_name)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    token = create_access_token({"sub": user["id"], "email": user["email"]})
    return TokenResponse(access_token=token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)


# ── Analysis endpoints ─────────────────────────────────────────────────────

@router.post("/run", response_model=AnalysisResponse)
def run_analysis_endpoint(
    payload: AnalysisRequest,
    current_user: dict = Depends(get_current_user),
):
    """Run selected analysis modules on an uploaded document."""
    if not payload.modules:
        raise HTTPException(status_code=400, detail="Select at least one analysis module.")

    results = run_analysis(payload.document_id, payload.modules)
    return AnalysisResponse(
        document_id=payload.document_id,
        status="completed",
        modules_run=payload.modules,
        results=results,
    )


@router.post("/query")
def semantic_query(
    payload: QueryRequest,
    current_user: dict = Depends(get_current_user),
):
    """Semantic search over an ingested document."""
    chunks = query_document(payload.document_id, payload.query, payload.top_k)
    return {"document_id": payload.document_id, "query": payload.query, "results": chunks}


# ── Document management endpoints ──────────────────────────────────────────

from utils.db import (
    list_documents,
    delete_document_chunks,
    document_exists,
    get_document_chunk_count,
)


@router.get("/documents", tags=["Documents"])
def list_all_documents(current_user: dict = Depends(get_current_user)):
    """List all documents currently stored in ChromaDB."""
    return {"documents": list_documents()}


@router.get("/documents/{document_id}", tags=["Documents"])
def get_document_info(document_id: str, current_user: dict = Depends(get_current_user)):
    """Get chunk count and existence status for a document."""
    exists = document_exists(document_id)
    return {
        "document_id": document_id,
        "exists": exists,
        "chunk_count": get_document_chunk_count(document_id) if exists else 0,
    }


@router.delete("/documents/{document_id}", tags=["Documents"])
def delete_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """Remove all chunks for a document from ChromaDB."""
    deleted = delete_document_chunks(document_id)
    return {"document_id": document_id, "chunks_deleted": deleted}