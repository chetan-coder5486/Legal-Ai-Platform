import uuid

from backend.services.document_rag import DocumentRAG


def generate_report(text: str, task_type: str) -> dict:
    """
    Orchestrator that routes the parsed document text to the appropriate AI pipeline
    and generates a final report.
    """
    report = {
        "task_type": task_type,
        "metadata": {"doc_length_chars": len(text)}
    }
    
    if task_type == "analyze_contract":
        from backend.pipelines.contract_analyzer import run_contract_analysis
        # Run base analysis
        analysis = run_contract_analysis(text)
        
      
        
        analyzed_clauses = analysis.get("analyzed_clauses", [])
        
        rag = DocumentRAG()

        document_id = str(uuid.uuid4())

        rag.ingest(
            document_id=document_id,
            analyzed_clauses=analysis["analyzed_clauses"]
        )

        analysis["document_id"] = document_id
        report["document_id"] = document_id
        print("Document ID:", document_id)

           
        report["contract_analysis"] = analysis
        
    elif task_type == "deep_research":
        from backend.services.explainability import generate_explanation
        # Use existing explanation block on the whole text if it's a clause
        report["research_data"] = generate_explanation({
            "clause_text": text,
            "risk_level": "RESEARCH",
            "risk_reason": "Deep inquiry"
        })
    else:
        raise ValueError(f"Unknown task type: {task_type}")
        
    return report

def route_document(text: str, task_type: str = "analyze_contract") -> dict:
    return generate_report(text, task_type)
