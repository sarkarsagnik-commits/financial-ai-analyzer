from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    file_size: int
    page_count: int
    chunks_stored: int
    message: str


class FinancialChangesResult(BaseModel):
    metrics: Dict[str, Any]
    yoy_changes: Dict[str, Any]
    summary: str


class RiskRadarResult(BaseModel):
    risk_factors: List[Dict[str, Any]]
    severity_breakdown: Dict[str, int]
    summary: str


class ManagementOutlookResult(BaseModel):
    tone: str
    tone_score: float
    key_themes: List[str]
    forward_guidance: List[str]
    summary: str


class AnalysisResponse(BaseModel):
    document_id: str
    status: str
    modules_run: List[str]
    results: Dict[str, Any]
    created_at: datetime = None

    def __init__(self, **data):
        if "created_at" not in data:
            data["created_at"] = datetime.utcnow()
        super().__init__(**data)


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None