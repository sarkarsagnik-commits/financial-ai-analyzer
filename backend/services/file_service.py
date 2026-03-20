import os
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
from config import settings

Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


def save_upload(file: UploadFile) -> dict:
    if file.content_type not in ("application/pdf",):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    document_id = str(uuid.uuid4())
    safe_name = f"{document_id}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        os.remove(file_path)
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit.",
        )

    return {
        "document_id": document_id,
        "filename": file.filename,
        "file_path": file_path,
        "file_size": file_size,
    }


def delete_document(document_id: str) -> bool:
    for fname in os.listdir(settings.UPLOAD_DIR):
        if fname.startswith(document_id):
            os.remove(os.path.join(settings.UPLOAD_DIR, fname))
            return True
    return False


def get_document_path(document_id: str) -> str:
    for fname in os.listdir(settings.UPLOAD_DIR):
        if fname.startswith(document_id):
            return os.path.join(settings.UPLOAD_DIR, fname)
    raise HTTPException(
        status_code=404, detail=f"Document {document_id} not found."
    )
