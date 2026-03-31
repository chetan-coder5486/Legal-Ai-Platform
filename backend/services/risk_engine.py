def assess_risk(clause_text: str, clause_type: str) -> dict:
    clause_lower = clause_text.lower()
    level = "LOW"
    reason = "Standard NDA language detected."

    if "definition of confidential" in clause_type.lower():
        if "oral" in clause_lower or "verbal" in clause_lower:
            level = "MEDIUM"
            reason = "Includes oral disclosures — harder to track and prove."
        elif "all information" in clause_lower or "any information" in clause_lower:
            level = "MEDIUM"
            reason = "Overly broad definition — may capture unintended information."

    elif "obligations of confidentiality" in clause_type.lower():
        if "perpetual" in clause_lower or "indefinitely" in clause_lower:
            level = "HIGH"
            reason = "Perpetual confidentiality obligation — no expiry defined."
        elif "reasonable" in clause_lower:
            level = "LOW"
            reason = "Standard reasonable care obligation."
        else:
            level = "MEDIUM"
            reason = "Obligation scope unclear — check duration and standard of care."

    elif "permitted disclosures" in clause_type.lower():
        if "prior written consent" in clause_lower:
            level = "LOW"
            reason = "Disclosure requires prior written consent — well controlled."
        elif "at its discretion" in clause_lower or "sole discretion" in clause_lower:
            level = "HIGH"
            reason = "One party has sole discretion to disclose — high risk."

    elif "term and duration" in clause_type.lower():
        if not any(w in clause_lower for w in ["year", "month", "date", "term"]):
            level = "HIGH"
            reason = "No clear duration specified — agreement may be open-ended."
        elif "2 year" in clause_lower or "two year" in clause_lower:
            level = "LOW"
            reason = "Standard 2-year term detected."

    elif "termination" in clause_type.lower():
        if "immediate" in clause_lower and "without" in clause_lower:
            level = "HIGH"
            reason = "Allows immediate termination without notice or cause."
        elif "notice" in clause_lower or "cure" in clause_lower:
            level = "LOW"
            reason = "Standard termination with notice period."

    elif "return or destruction" in clause_type.lower():
        if "destroy" not in clause_lower and "return" not in clause_lower:
            level = "MEDIUM"
            reason = "No explicit return or destruction obligation found."
        else:
            level = "LOW"
            reason = "Return/destruction of confidential materials addressed."

    elif "governing law" in clause_type.lower():
        if not any(w in clause_lower for w in ["england", "wales", "scotland",
                                                 "delaware", "california",
                                                 "new york", "india"]):
            level = "MEDIUM"
            reason = "Jurisdiction is unusual or unclear — verify with counsel."

    elif "remedies" in clause_type.lower():
        if "injunctive" in clause_lower or "equitable" in clause_lower:
            level = "LOW"
            reason = "Standard injunctive relief provision."
        elif "unlimited" in clause_lower:
            level = "HIGH"
            reason = "Unlimited remedies clause — significant financial exposure."

    elif "intellectual property" in clause_type.lower():
        if "assign" in clause_lower or "transfer" in clause_lower:
            level = "HIGH"
            reason = "IP assignment detected — ownership may transfer to other party."
        elif "license" in clause_lower:
            level = "MEDIUM"
            reason = "License grant found — review scope and exclusivity."

    return {"level": level, "reason": reason}