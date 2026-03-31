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
    Upload a document and route it to the correct AI pipeline.
    """

    try:
        # 1️⃣ Read file
        file_bytes = await file.read()

        # 2️⃣ Parse document → text
        text = parse_document(file.filename, file_bytes)

        if text is None or text.strip() == "":
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from document."
            )

        # 3️⃣ Route to correct pipeline
        try:
            result = route_document(text, task_type=task_type)
        except Exception as e:
            result = {
                "message": "Pipeline not fully implemented yet",
                "preview": text[:500] + "...",
                "error": str(e)
            }

        # 4️⃣ Return response (don't send full parsed text — can be huge)
        return {
            "status": "success",
            "filename": file.filename,
            "task": task_type,
            "results": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))