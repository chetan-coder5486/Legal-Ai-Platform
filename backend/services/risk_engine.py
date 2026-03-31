import re


def assess_risk(clause_text: str, clause_type: str) -> dict:
    """
    Advanced rule-based risk engine with scoring + multi-signal detection.

    Features:
    - Scoring-based risk classification (LOW / MEDIUM / HIGH)
    - Detects multiple risk signals in a single clause
    - Works even if classification is slightly wrong
    - Produces meaningful explanations
    """

    text = clause_text.lower()
    score = 0
    reasons = []

    # --------------------------------------------------
    # 🔴 LIABILITY RISKS
    # --------------------------------------------------
    if "unlimited liability" in text or "without limit" in text:
        score += 5
        reasons.append("Unlimited liability exposure")

    if "indirect damages" in text and "exclude" not in text:
        score += 3
        reasons.append("Indirect damages not excluded")

    if "consequential damages" in text and "exclude" not in text:
        score += 3
        reasons.append("Consequential damages not excluded")

    if "cap" in text or "limited to" in text:
        score -= 1  # reduces risk slightly

    # --------------------------------------------------
    # 🔴 TERMINATION RISKS
    # --------------------------------------------------
    if "without cause" in text:
        score += 4
        reasons.append("Termination allowed without cause")

    if "immediate termination" in text:
        score += 3
        reasons.append("Immediate termination clause")

    if "notice" not in text and clause_type == "Termination":
        score += 2
        reasons.append("No notice period defined")

    if "cure period" in text:
        score -= 1  # safer clause

    # --------------------------------------------------
    # 🔴 CONFIDENTIALITY RISKS
    # --------------------------------------------------
    year_match = re.search(r'(\d+)\s+year', text)
    if year_match:
        years = int(year_match.group(1))
        if years >= 5:
            score += 2
            reasons.append(f"Long confidentiality duration ({years} years)")

    if "perpetual" in text:
        score += 3
        reasons.append("Perpetual confidentiality obligation")

    # --------------------------------------------------
    # 🔴 PAYMENT RISKS
    # --------------------------------------------------
    if "late fee" not in text and clause_type == "Payment":
        score += 2
        reasons.append("No late fee protection")

    if "non-refundable" in text:
        score += 2
        reasons.append("Non-refundable payment terms")

    # --------------------------------------------------
    # 🔴 GOVERNING LAW RISKS
    # --------------------------------------------------
    if clause_type == "Governing Law":
        if not any(j in text for j in ["india", "delaware", "california", "new york"]):
            score += 2
            reasons.append("Unfamiliar or foreign jurisdiction")

    # --------------------------------------------------
    # 🔴 ONE-SIDED CLAUSE DETECTION
    # --------------------------------------------------
    if "receiving party shall" in text and "disclosing party shall" not in text:
        score += 2
        reasons.append("One-sided obligation")

    if "sole discretion" in text:
        score += 2
        reasons.append("Unilateral decision power")

    # --------------------------------------------------
    # 🔴 INTELLECTUAL PROPERTY RISKS
    # --------------------------------------------------
    if "transfer of ownership" in text:
        score += 3
        reasons.append("Potential IP ownership transfer")

    if "royalty-free" in text and "irrevocable" in text:
        score += 3
        reasons.append("Irrevocable royalty-free license")

    # --------------------------------------------------
    # 🔴 FORCE MAJEURE RISKS
    # --------------------------------------------------
    if clause_type == "Force Majeure":
        if "pandemic" not in text and "government" not in text:
            score += 1
            reasons.append("Force majeure scope may be limited")

    # --------------------------------------------------
    # 🧠 FINAL RISK LEVEL
    # --------------------------------------------------
    if score >= 5:
        level = "HIGH"
    elif score >= 3:
        level = "MEDIUM"
    else:
        level = "LOW"

    # --------------------------------------------------
    # 🧾 DEFAULT SAFE MESSAGE
    # --------------------------------------------------
    if not reasons:
        reasons.append("No unusual or risky patterns detected")

    return {
        "level": level,
        "reason": "; ".join(reasons)
    }