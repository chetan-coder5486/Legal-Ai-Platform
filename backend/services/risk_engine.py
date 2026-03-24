def assess_risk(clause_text: str, clause_type: str) -> dict:
    """
    Rule-based engine to determine risk based on clause content and classified type.
    """
    clause_lower = clause_text.lower()
    
    level = "LOW"
    reason = "Standard language detected."
    
    if clause_type == "Liability":
        if "unlimited" in clause_lower or "without limit" in clause_lower:
            level = "HIGH"
            reason = "Unlimited liability detected. Exposes the company to uncapped financial damages."
        elif "cap" in clause_lower or "limited to" in clause_lower:
            level = "LOW"
            reason = "Liability is capped."
        else:
            level = "MEDIUM"
            reason = "Liability terms ambiguous. Needs manual review for financial caps."
            
    elif clause_type == "Termination":
        if "immediate" in clause_lower and "without cause" in clause_lower:
            level = "HIGH"
            reason = "Allows immediate termination without cause. High risk to revenue stability."
        elif "cure period" in clause_lower or "notice" in clause_lower:
            level = "LOW"
            reason = "Standard termination with notice or cure period."
            
    elif clause_type == "Governing Law":
        if "delaware" not in clause_lower and "california" not in clause_lower:
            level = "MEDIUM"
            reason = "Unusual jurisdiction detected. Verify counsel approval."
            
    return {"level": level, "reason": reason}
