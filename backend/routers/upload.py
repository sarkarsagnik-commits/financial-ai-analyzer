from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks
from models.response_models import UploadResponse
from services.file_service import save_upload
from services.analysis_service import ingest_document
from utils.jwt_handler import get_current_user

router = APIRouter()


@router.post("/", response_model=UploadResponse, status_code=202)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
):
    """Upload a PDF and queue it for background ingestion into ChromaDB."""
    # 1. Save file to disk (fast, synchronous)
    meta = save_upload(file)

    # 2. Queue ingestion as a background task (non-blocking)
    background_tasks.add_task(
        ingest_document,
        document_id=meta["document_id"],
        file_path=meta["file_path"],
        filename=meta["filename"],
        user_id=current_user.get("sub", ""),
    )

    # 3. Return immediately — ingestion continues in background
    return UploadResponse(
        document_id=meta["document_id"],
        filename=meta["filename"],
        file_size=meta["file_size"],
        page_count=0,
        chunks_stored=0,
        message="Document uploaded. Ingestion is processing in the background.",
    )