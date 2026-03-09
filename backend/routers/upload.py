from fastapi import APIRouter, UploadFile, File, Depends
from models.response_models import UploadResponse
from services.file_service import save_upload
from services.analysis_service import ingest_document
from utils.jwt_handler import get_current_user

router = APIRouter()


@router.post("/", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload a PDF and ingest it into ChromaDB."""
    # 1. Save file to disk
    meta = save_upload(file)

    # 2. Ingest: extract text → chunk → store in ChromaDB
    ingestion = ingest_document(
        document_id=meta["document_id"],
        file_path=meta["file_path"],
        filename=meta["filename"],
        user_id=current_user.get("sub", ""),
    )

    return UploadResponse(
        document_id=meta["document_id"],
        filename=meta["filename"],
        file_size=meta["file_size"],
        page_count=ingestion.get("page_count", 0),
        chunks_stored=ingestion.get("chunks_stored", 0),
        message=f"Status: {ingestion['status']}. Document ready for analysis.",
    )