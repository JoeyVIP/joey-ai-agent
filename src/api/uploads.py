import logging
import os
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/uploads", tags=["Uploads"])
logger = logging.getLogger(__name__)

# Upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Max file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed extensions
ALLOWED_EXTENSIONS = {
    ".txt", ".md", ".py", ".js", ".ts", ".jsx", ".tsx",
    ".json", ".yaml", ".yml", ".toml", ".env",
    ".html", ".css", ".scss", ".sql",
    ".sh", ".bash", ".dockerfile", ".gitignore"
}


def validate_file(file: UploadFile) -> None:
    """驗證上傳檔案"""
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支援的檔案類型: {file_ext}"
        )


@router.post("/files")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    上傳多個檔案
    Returns: [{"filename": "xxx", "path": "uploads/xxx", "size": 1234}]
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    uploaded_files = []

    for file in files:
        try:
            # Validate
            validate_file(file)

            # Read content
            content = await file.read()

            # Check size
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"檔案 {file.filename} 超過大小限制 (10MB)"
                )

            # Save file
            file_path = UPLOAD_DIR / file.filename
            with open(file_path, "wb") as f:
                f.write(content)

            uploaded_files.append({
                "filename": file.filename,
                "path": str(file_path),
                "size": len(content)
            })

            logger.info(f"Uploaded file: {file.filename} ({len(content)} bytes)")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to upload {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"上傳失敗: {file.filename}"
            )

    return {
        "success": True,
        "files": uploaded_files,
        "total": len(uploaded_files)
    }


@router.get("/files/{filename}")
async def download_file(filename: str):
    """下載已上傳的檔案"""
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )


@router.delete("/files/{filename}")
async def delete_file(filename: str):
    """刪除已上傳的檔案"""
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        file_path.unlink()
        logger.info(f"Deleted file: {filename}")
        return {"success": True, "message": f"Deleted {filename}"}
    except Exception as e:
        logger.error(f"Failed to delete {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete file")
