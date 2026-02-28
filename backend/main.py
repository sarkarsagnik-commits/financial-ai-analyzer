from fastapi import FastAPI
from backend.routers import upload

app = FastAPI()

app.include_router(upload.router)

@app.get("/health")
def health_check():
    return {"status": "running"}
from backend.routers import upload, analysis
app.include_router(upload.router)
app.include_router(analysis.router)