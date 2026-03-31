def generate_report(text: str, task_type: str) -> dict:
    """
    Orchestrator that routes the parsed document text to the appropriate AI pipeline
    and generates a final report.
    """
    from backend.pipelines.summarizer import run_summarization
    from backend.pipelines.contract_analyzer import run_contract_analysis
    from backend.services.explainability import generate_explanation
    
    report = {
        "task_type": task_type,
        "metadata": {"doc_length_chars": len(text)}
    }
    
    if task_type == "summarize_case":
        report["summary_data"] = run_summarization(text)
        
    elif task_type == "analyze_contract":
        # Run base analysis
        analysis = run_contract_analysis(text)
        
      
        
        analyzed_clauses = analysis.get("analyzed_clauses", [])
            
        report["contract_analysis"] = analysis
        
    elif task_type == "deep_research":
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
