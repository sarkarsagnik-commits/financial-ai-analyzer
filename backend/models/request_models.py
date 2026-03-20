from pydantic import BaseModel, EmailStr
from typing import List, Optional


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class AnalysisRequest(BaseModel):
    document_id: str
    modules: List[str]  # ["Financial Changes", "Risk Radar", "Management Outlook"]
    user_id: Optional[str] = None


class QueryRequest(BaseModel):
    document_id: str
    query: str
    top_k: int = 5


# --- RAG (from feature/RAG) ---

class RAGQueryRequest(BaseModel):
    query: str
    document_id: Optional[str] = None
