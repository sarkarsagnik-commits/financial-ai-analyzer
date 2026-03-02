from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import uuid

router = APIRouter()

UPLOAD_DIR = "backend/data"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    if file is None or file.filename is None:
        raise HTTPException(status_code=400, detail="No file uploaded")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")

    try:
        contents = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "File uploaded successfully",
        "file_id": file_id
    }