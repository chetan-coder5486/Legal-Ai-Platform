from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import Dict, Any, List
from pydantic import BaseModel
from backend.services.parsers import parse_document
from backend.services.orchestrator import route_document
from backend.services.explainability import generate_explanation
from backend.services.redraft_clause import generate_redraft          # NEW
from backend.pipelines.research_agent import ingest_document

router = APIRouter()


# ── Request models ────────────────────────────────────────────────────────────

class ClauseRequest(BaseModel):
    clause_text: str
    clause_type: str
    risk_level: str
    risk_reason: str


class PrecedentRequest(BaseModel):
    clause_text: str


class RedraftRequest(BaseModel):          # NEW
    clause_text: str
    clause_type: str
    risk_level: str
    risk_reason: str
    recommendations: List[str] = []


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    task_type: str = Form("analyze_contract"),
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
                detail="Could not extract text from document.",
            )

        # Continual Learning: ingest into ChromaDB in the background
        if task_type in ("analyze_contract", "summarize_case"):
            background_tasks.add_task(ingest_document, file.filename, text)

        try:
            result = route_document(text, task_type=task_type)
        except Exception as e:
            result = {
                "message": "Pipeline not fully implemented yet",
                "preview": text[:500] + "...",
                "error": str(e),
            }

        return {
            "status": "success",
            "filename": file.filename,
            "task": task_type,
            "results": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain-clause")
async def explain_clause(req: ClauseRequest) -> Dict[str, Any]:
    """
    Explains a single clause on demand via Groq.
    Called when the user clicks the 'Explain clause' button.
    """
    try:
        result = generate_explanation(
            {
                "clause_text": req.clause_text,
                "type": req.clause_type,
                "risk_level": req.risk_level,
                "risk_reason": req.risk_reason,
            }
        )
        return {
            "status": "success",
            "explanation": result.get("explanation", "No explanation generated."),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/redraft-clause")          # NEW
async def redraft_clause(req: RedraftRequest) -> Dict[str, Any]:
    """
    Suggests a safer redraft of a risky clause via Groq.
    Called when the user clicks 'Suggest safer redraft'.
    Only offered for HIGH and MEDIUM risk clauses (enforced in the UI too).
    """
    try:
        redraft_text = generate_redraft(
            clause_text=req.clause_text,
            clause_type=req.clause_type,
            risk_level=req.risk_level,
            risk_reason=req.risk_reason,
            recommendations=req.recommendations,
        )
        return {
            "status": "success",
            "redraft": redraft_text,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/find-precedents")
async def find_precedents(req: PrecedentRequest) -> Dict[str, Any]:
    """
    Looks up similar past clauses from ChromaDB vector store.
    """
    try:
        from backend.pipelines.research_agent import search_precedents
        results = search_precedents(req.clause_text, top_k=3)
        return {
            "status": "success",
            "precedents": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
