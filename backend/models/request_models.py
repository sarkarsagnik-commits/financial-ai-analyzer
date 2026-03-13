from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    query: str