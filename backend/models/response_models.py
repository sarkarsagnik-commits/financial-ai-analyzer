from pydantic import BaseModel


class AnalysisResponse(BaseModel):
    summary: str
    key_insights: str
    investment_advice: str