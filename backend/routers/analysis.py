from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

router = APIRouter()


class AnalyzeRequest(BaseModel):
    file_id: str
    features: list[str]


@router.post("/analyze")
def analyze_file(request: AnalyzeRequest):
    file_path = f"backend/data/{request.file_id}.pdf"

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    dummy_response = {}

    if "delta" in request.features:
        dummy_response["delta"] = "Revenue increased 12% YoY. Net income up 8%."

    if "risk" in request.features:
        dummy_response["risk"] = "Increased exposure to macroeconomic volatility."

    if "summary" in request.features:
        dummy_response["summary"] = "Overall performance stable with moderate growth."

    return {
        "file_id": request.file_id,
        "analysis": dummy_response
    }