from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import Dict, Any
from pydantic import BaseModel
from backend.services.parsers import parse_document
from backend.services.orchestrator import route_document
from backend.services.explainability import generate_explanation
from backend.pipelines.research_agent import ingest_document

router = APIRouter()


class ClauseRequest(BaseModel):
    clause_text: str
    clause_type: str
    risk_level: str
    risk_reason: str


class PrecedentRequest(BaseModel):
    clause_text: str

@router.post("/find-precedents")
async def find_precedents(req: PrecedentRequest) -> Dict[str, Any]:
    """
    Looks up similar past clauses from ChromaDB.
    """
    try:
        from backend.pipelines.research_agent import search_precedents
        results = search_precedents(req.clause_text, top_k=3)
        return {
            "status": "success",
            "precedents": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    task_type: str = Form("analyze_contract")
) -> Dict[str, Any]:
    """
    Upload a document and route it to the correct AI pipeline.
    """
    try:
        file_bytes = await file.read()
        text = parse_document(file.filename, file_bytes)

        if not text or text.strip() == "":
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from document."
            )

        # Continual Learning: Add to local Vector database in the background
        if task_type in ("analyze_contract", "summarize_case"):
            background_tasks.add_task(ingest_document, file.filename, text)

        try:
            result = route_document(text, task_type=task_type)
        except Exception as e:
            result = {
                "message": "Pipeline not fully implemented yet",
                "preview": text[:500] + "...",
                "error": str(e)
            }

        return {
            "status": "success",
            "filename": file.filename,
            "task": task_type,
            "results": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain-clause")
async def explain_clause(req: ClauseRequest) -> Dict[str, Any]:
    """
    Explains a single clause on demand.
    Only called when user clicks the Explain button.
    """
    try:
        result = generate_explanation({
            "clause_text": req.clause_text,
            "type": req.clause_type,
            "risk_level": req.risk_level,
            "risk_reason": req.risk_reason
        })
        return {
            "status": "success",
            "explanation": result.get("explanation", "No explanation generated.")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))