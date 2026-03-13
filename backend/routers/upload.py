from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Dict, Any
from backend.services.parsers import parse_document
from backend.services.orchestrator import route_document

router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    task_type: str = Form("analyze_contract")
) -> Dict[str, Any]:

    """
    Endpoint to upload a document (PDF, DOCX, TXT) and trigger a specific workflow pipeline.
    """
    try:
        # Read file bytes
        file_bytes = await file.read()
        
        # 1. Parse document into clean text
        text = parse_document(file.filename, file_bytes)
        
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from document.")
            
        # 2. Route to orchestrator to run the correct pipeline
        # (For now, since pipelines aren't fully implemented, this might just return a mock or fail if not handled)
        # We will wrap it in a try-except to return the raw text if pipelines are missing.
        try:
            result = route_document(text, task_type=task_type)
        except Exception as e:
            # Fallback for now during development: just return the extracted text snippet
            result = {
                "message": "Pipeline not fully implemented yet.",
                "preview": text[:500] + "...",
                "error_details": str(e)
            }
            
        return {
            "status": "success",
            "filename": file.filename,
            "task": task_type,
            "results": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
