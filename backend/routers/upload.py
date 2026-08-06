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
    document_id: str
    clause_text: str
    clause_id: str | None = None


class ChatRequest(BaseModel):
    document_id: str
    question: str
    top_k: int = 5


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
        if task_type == "analyze_contract":
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
    Looks up similar clauses within the current document's RAG collection.
    """
    try:
        from backend.services.document_rag import DocumentRAG

        rag = DocumentRAG()
        results = rag.search(
            document_id=req.document_id,
            query=req.clause_text,
            top_k=3,
            exclude_clause_id=req.clause_id,
        )
        return {
            "status": "success",
            "precedents": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask-document")
async def ask_document(req: ChatRequest) -> Dict[str, Any]:
    """
    Answers contract questions using the uploaded document's own RAG collection.
    """
    try:
        from backend.services.document_rag import DocumentRAG

        rag = DocumentRAG()
        result = rag.ask(
            document_id=req.document_id,
            question=req.question,
            top_k=req.top_k,
        )

        return {
            "status": "success",
            **result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
