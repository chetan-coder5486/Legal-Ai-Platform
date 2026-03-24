from backend.pipelines.research_agent import search_precedents

def generate_explanation(risk_analysis: dict) -> dict:
    \"\"\"
    Combines outputs from the Risk Engine and Research Agent to provide a human-readable explanation.
    \"\"\"
    clause_text = risk_analysis.get("clause_text", "")
    risk_level = risk_analysis.get("risk_level", "LOW")
    risk_reason = risk_analysis.get("risk_reason", "")
    
    # If the risk is high or medium, fetch precedent
    precedents = []
    if risk_level in ["HIGH", "MEDIUM"]:
        precedents = search_precedents(clause_text, top_k=1)
        
    human_explanation = (
        f"Clause flagged as {risk_level} RISK.\n"
        f"Reason: {risk_reason}\n\n"
    )
    
    if precedents:
        human_explanation += "Relevant precedent:\n"
        for p in precedents:
            source = p.get('metadata', {}).get('source', "Case Law")
            text_snippet = p.get('text', '')[:100] + "..."
            human_explanation += f"{source} - {text_snippet}\n"
            
    risk_analysis["explanation"] = human_explanation
    risk_analysis["precedents_found"] = precedents
    
    return risk_analysis
