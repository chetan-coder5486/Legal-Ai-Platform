def assess_risk(clause_text: str, clause_type: str) -> dict:
    """
    Rule-based engine to determine risk based on clause content and classified type.
    Supports: Termination, Liability, Governing Law, Payment, Warranty, Confidentiality
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
        elif "without notice" in clause_lower:
            level = "HIGH"
            reason = "Termination without notice period. High risk."
        elif "cure period" in clause_lower or "notice" in clause_lower:
            level = "LOW"
            reason = "Standard termination with notice or cure period."
        else:
            level = "MEDIUM"
            reason = "Termination terms need review. No clear notice/cure period specified."

    elif clause_type == "Governing Law":
        if "delaware" not in clause_lower and "california" not in clause_lower:
            level = "MEDIUM"
            reason = "Unusual jurisdiction detected. Verify counsel approval."

    elif clause_type == "Payment":
        if "late fee" in clause_lower or "penalty" in clause_lower or "interest" in clause_lower:
            level = "MEDIUM"
            reason = "Payment clause includes penalty/interest terms. Review financial exposure."
        elif "net 90" in clause_lower or "net 120" in clause_lower:
            level = "MEDIUM"
            reason = "Extended payment terms detected (90+ days). Cash flow risk."
        elif "immediate" in clause_lower and "upon" in clause_lower:
            level = "LOW"
            reason = "Standard immediate payment terms."

    elif clause_type == "Warranty":
        if "as is" in clause_lower or "no warranty" in clause_lower or "without warranty" in clause_lower:
            level = "HIGH"
            reason = "Disclaimer of all warranties. No recourse if deliverables fail."
        elif "limited warranty" in clause_lower:
            level = "MEDIUM"
            reason = "Limited warranty. Review scope and duration of coverage."
        elif "warrant" in clause_lower and ("12 month" in clause_lower or "one year" in clause_lower):
            level = "LOW"
            reason = "Standard warranty period."

    elif clause_type == "Confidentiality":
        if "perpetual" in clause_lower or "indefinite" in clause_lower or "survive" in clause_lower:
            level = "MEDIUM"
            reason = "Confidentiality obligations may be perpetual. Review duration and scope."
        elif "non-disclosure" in clause_lower or "nda" in clause_lower:
            level = "LOW"
            reason = "Standard non-disclosure terms."
        elif "injunctive" in clause_lower:
            level = "MEDIUM"
            reason = "Allows injunctive relief for confidentiality breach. Review scope."

    return {"level": level, "reason": reason}
