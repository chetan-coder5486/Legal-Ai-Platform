import re

def assess_risk(clause_text: str, clause_type: str) -> dict:
    text = clause_text.lower()
    score = 0
    reasons = []

    # -----------------------------
    # 🔴 LIABILITY
    # -----------------------------
    if (
        "unlimited liability" in text or
        "without limit" in text or
        ("liability" in text and "no limit" in text)
    ):
        score += 5
        reasons.append("Unlimited liability exposure")

    if "indirect damages" in text and "exclude" not in text:
        score += 2
        reasons.append("Indirect damages not excluded")

    if "consequential damages" in text and "exclude" not in text:
        score += 2
        reasons.append("Consequential damages not excluded")

    if "cap" in text or "limited to" in text:
        score -= 1

    # -----------------------------
    # 🔴 TERMINATION
    # -----------------------------
    if "without cause" in text:
        score += 3
        reasons.append("Termination without cause")

    if "immediate termination" in text:
        score += 2
        reasons.append("Immediate termination")

    if "notice" not in text and clause_type == "Termination":
        score += 2
        reasons.append("No notice period")

    if "cure period" in text:
        score -= 1

    # -----------------------------
    # 🔴 CONFIDENTIALITY
    # -----------------------------
    year_match = re.search(r'(\d+)\s+year', text)
    if year_match:
        years = int(year_match.group(1))
        if years >= 5:
            score += 2
            reasons.append(f"Long duration ({years} years)")
        elif years >= 2:
            score += 1

    if "perpetual" in text:
        score += 3
        reasons.append("Perpetual obligation")

    # -----------------------------
    # 🔴 PAYMENT
    # -----------------------------
    if clause_type == "Payment":
        if "late fee" not in text:
            score += 1
            reasons.append("No late fee protection")

        if "non-refundable" in text:
            score += 2
            reasons.append("Non-refundable terms")

    # -----------------------------
    # 🔴 GOVERNING LAW
    # -----------------------------
    if clause_type == "Governing Law":
        if "india" not in text:
            score += 2
            reasons.append("Foreign jurisdiction")

    # -----------------------------
    # 🔴 LEGAL / COMPLIANCE (🔥 NEW - IMPORTANT)
    # -----------------------------
    if "required by law" in text or "court order" in text or "regulatory" in text:
        score += 2
        reasons.append("Mandatory legal disclosure")

    # -----------------------------
    # 🔴 DATA / RETURN OBLIGATIONS (🔥 NEW)
    # -----------------------------
    if "return or destroy" in text:
        score += 2
        reasons.append("Strict data return obligation")

    if "certify in writing" in text:
        score += 1
        reasons.append("Formal compliance requirement")

    # -----------------------------
    # 🔴 DURATION / SURVIVAL (🔥 NEW)
    # -----------------------------
    if "survive termination" in text or "continuing obligations" in text:
        score += 2
        reasons.append("Obligations survive termination")

    # -----------------------------
    # 🔴 INJUNCTIVE RELIEF (🔥 NEW - VERY IMPORTANT)
    # -----------------------------
    if "injunctive relief" in text or "irreparable harm" in text:
        score += 2
        reasons.append("Injunctive relief clause")

    # -----------------------------
    # 🔴 ONE-SIDED (IMPROVED)
    # -----------------------------
    if (
        "receiving party shall" in text and
        "disclosing party shall" not in text
    ):
        score += 2
        reasons.append("One-sided obligation")

    # broader detection
    if "shall" in text and "other party shall" not in text:
        score += 1

    if "sole discretion" in text:
        score += 2
        reasons.append("Unilateral control")

    # -----------------------------
    # 🔴 IP
    # -----------------------------
    if "transfer of ownership" in text:
        score += 3
        reasons.append("Ownership transfer")

    if "royalty-free" in text and "irrevocable" in text:
        score += 3
        reasons.append("Irrevocable license")

    # -----------------------------
    # 🔴 FORCE MAJEURE
    # -----------------------------
    if clause_type == "Force Majeure":
        if "pandemic" not in text:
            score += 1
            reasons.append("Limited force majeure scope")

    # -----------------------------
    # 🧠 FINAL THRESHOLDS
    # -----------------------------
    if score >= 6:
        level = "HIGH"
    elif score >= 3:
        level = "MEDIUM"
    else:
        level = "LOW"

    if not reasons:
        reasons.append("Standard clause")

    return {
        "level": level,
        "reason": "; ".join(reasons)
    }