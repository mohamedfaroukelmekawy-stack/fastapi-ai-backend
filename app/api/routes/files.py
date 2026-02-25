from fastapi import APIRouter, UploadFile, File, Depends
from app.core.security import get_current_user_id
from app.services.file_service import FileService
from app.services.embedding_service import EmbeddingService

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/analyze")
async def analyze_file(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
):
    """
    Upload image or PDF:
    1. Describes image / extracts PDF text
    2. Auto generates embedding from description
    3. Stores embedding in Supabase
    """
    content = await FileService().extract_content(file)
    embedding_result = EmbeddingService().create_and_store(user_id, content)

    return {
        "filename": file.filename,
        "description": content,
        "embedding_id": embedding_result["id"],
        "embedding_size": embedding_result["embedding_size"],
        "message": "File analyzed and embedding stored successfully"
    }
