from fastapi import APIRouter
from backend.models.request_models import AnalysisRequest
from backend.models.response_models import AnalysisResponse
from backend.services.analysis_service import analyze_financial_report

router = APIRouter()


@router.post("/analysis", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):

    # In production this text will come from parser
    parsed_text = "Financial report text goes here"

    result = analyze_financial_report(parsed_text, request.query)

    return AnalysisResponse(
        summary=result,
        key_insights="Generated insights",
        investment_advice="Generated advice",
    )