import re


WORD_TO_NUMBER = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def _normalize_clause_type(clause_type: str) -> str:
    normalized = (clause_type or "").strip().lower()

    if "termination" in normalized:
        return "termination"
    if "governing law" in normalized or "jurisdiction" in normalized:
        return "governing_law"
    if "force majeure" in normalized:
        return "force_majeure"
    if "payment" in normalized:
        return "payment"
    if "liability" in normalized:
        return "liability"
    if "intellectual property" in normalized or "ownership" in normalized or "license" in normalized:
        return "ip"
    if "confidential" in normalized or "non-disclosure" in normalized:
        return "confidentiality"
    if "return or destruction" in normalized:
        return "return_of_information"
    if "injunctive relief" in normalized or "remedies" in normalized:
        return "remedies"
    if "term and duration" in normalized or "duration" in normalized:
        return "duration"
    return normalized


def _extract_years(text: str):
    digit_with_parens_match = re.search(r"\b[a-z]+\s*\((\d+)\)\s*year[s]?\b", text)
    if digit_with_parens_match:
        return int(digit_with_parens_match.group(1))

    digit_match = re.search(r"\b(\d+)\s+year[s]?\b", text)
    if digit_match:
        return int(digit_match.group(1))

    word_match = re.search(r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+year[s]?\b", text)
    if word_match:
        return WORD_TO_NUMBER[word_match.group(1)]

    return None


def _append_unique(items: list, value: str) -> None:
    if value not in items:
        items.append(value)


def _extract_evidence(text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return ""


def _add_risk(
    matched_rules: list,
    reasons: list,
    recommendations: list,
    rule_id: str,
    label: str,
    impact: int,
    evidence: str,
    recommendation: str | None = None,
) -> int:
    matched_rules.append(
        {
            "rule_id": rule_id,
            "label": label,
            "impact": impact,
            "evidence": evidence,
        }
    )
    reasons.append(label)
    if recommendation:
        _append_unique(recommendations, recommendation)
    return impact


def _add_positive(positive_signals: list, label: str, evidence: str, impact: int = 0) -> None:
    positive_signals.append(
        {
            "label": label,
            "evidence": evidence,
            "impact": impact,
        }
    )


def _summarize_clause(level: str, reasons: list, positives: list) -> str:
    if reasons:
        if len(reasons) == 1 and reasons[0] == "Standard clause":
            return "No major risk signals detected."
        return f"{level} risk driven by: {', '.join(reasons[:3])}."
    if positives:
        labels = ", ".join(item["label"] for item in positives[:2])
        return f"{level} risk with protective signals such as {labels}."
    return "LOW risk with no major red flags detected."


def assess_risk(clause_text: str, clause_type: str) -> dict:
    text = (clause_text or "").lower()
    category = _normalize_clause_type(clause_type)
    score = 0
    reasons = []
    matched_rules = []
    positive_signals = []
    recommendations = []

    if (
        "unlimited liability" in text
        or ("liability" in text and re.search(r"\bunlimited\b|\bwithout\s+financial\s+cap\b|\bwithout\s+any\s+cap\b|\bno\s+limit\b", text))
        or re.search(r"\bwithout\s+(?:financial\s+)?limit\b", text)
    ):
        score += _add_risk(
            matched_rules,
            reasons,
            recommendations,
            "liability_unlimited",
            "Unlimited liability exposure",
            6,
            _extract_evidence(text, [r"unlimited liability", r"\bwithout\s+(?:financial\s+)?limit\b", r"no limit"]),
            "Add a clear monetary cap on liability tied to fees paid or a fixed amount.",
        )

    if "indirect damages" in text and "exclude" not in text:
        score += _add_risk(
            matched_rules,
            reasons,
            recommendations,
            "damages_indirect",
            "Indirect damages not excluded",
            2,
            "indirect damages",
            "Exclude indirect and special damages where commercially possible.",
        )

    if "consequential damages" in text and "exclude" not in text:
        score += _add_risk(
            matched_rules,
            reasons,
            recommendations,
            "damages_consequential",
            "Consequential damages not excluded",
            2,
            "consequential damages",
            "Add an exclusion for consequential damages.",
        )

    if re.search(r"\bliability cap\b|\bcapped at\b|\blimited to\b", text):
        score -= 1
        _add_positive(
            positive_signals,
            "Liability cap present",
            _extract_evidence(text, [r"liability cap", r"capped at", r"limited to"]),
            -1,
        )

    if "exclude" in text and ("indirect damages" in text or "consequential damages" in text):
        _add_positive(
            positive_signals,
            "Damages exclusion present",
            _extract_evidence(text, [r"exclude.{0,40}indirect damages", r"exclude.{0,40}consequential damages"]),
        )

    if "without cause" in text:
        score += _add_risk(
            matched_rules,
            reasons,
            recommendations,
            "termination_without_cause",
            "Termination without cause",
            3,
            "without cause",
            "Require a minimum written notice period for no-cause termination.",
        )

    if "immediate termination" in text or re.search(r"\bterminate\b.{0,20}\bimmediately\b", text):
        score += _add_risk(
            matched_rules,
            reasons,
            recommendations,
            "termination_immediate",
            "Immediate termination",
            2,
            "immediate termination",
            "Limit immediate termination to material breach, illegality, or serious misconduct.",
        )

    if category == "termination" and ("without notice" in text or "no notice" in text):
        score += _add_risk(
            matched_rules,
            reasons,
            recommendations,
            "termination_without_notice",
            "Termination without notice",
            2,
            _extract_evidence(text, [r"without notice", r"no notice"]),
            "Add a notice requirement such as 15 to 30 days before termination takes effect.",
        )
    elif category == "termination" and "notice" not in text:
        score += _add_risk(
            matched_rules,
            reasons,
            recommendations,
            "termination_no_notice",
            "No notice period",
            2,
            "notice not found",
            "Add a notice requirement such as 15 to 30 days before termination takes effect.",
        )
    elif category == "termination" and "notice" in text:
        _add_positive(
            positive_signals,
            "Notice period present",
            _extract_evidence(text, [r"\bnotice\b"]),
        )

    if "cure period" in text:
        score -= 1
        _add_positive(
            positive_signals,
            "Cure period present",
            "cure period",
            -1,
        )

    years = _extract_years(text)
    if years is not None:
        if years >= 5:
            score += _add_risk(
                matched_rules,
                reasons,
                recommendations,
                "duration_long",
                f"Long duration ({years} years)",
                2,
                f"{years} years",
                "Consider narrowing the confidentiality survival period unless trade secrets require longer coverage.",
            )
        elif years >= 2:
            score += _add_risk(
                matched_rules,
                reasons,
                recommendations,
                "duration_moderate",
                f"Moderate duration ({years} years)",
                1,
                f"{years} years",
            )
        else:
            _add_positive(
                positive_signals,
                f"Short duration ({years} years)",
                f"{years} years",
            )

    if "perpetual" in text:
        score += _add_risk(
            matched_rules,
            reasons,
            recommendations,
            "duration_perpetual",
            "Perpetual obligation",
            3,
            "perpetual",
            "Limit perpetual obligations to trade secrets instead of all confidential information.",
        )

    if "required by law" in text or "court order" in text:
        _add_positive(
            positive_signals,
            "Standard legal disclosure carve-out",
            _extract_evidence(text, [r"required by law", r"court order"]),
        )

    if category == "payment":
        if "non-refundable" in text:
            score += _add_risk(
                matched_rules,
                reasons,
                recommendations,
                "payment_non_refundable",
                "Non-refundable terms",
                2,
                "non-refundable",
                "Tie non-refundable amounts to defined milestones or services actually delivered.",
            )

    if category == "governing_law":
        known_jurisdictions = [
            "india", "england", "wales", "scotland", "uk", "united kingdom",
            "delaware", "california", "new york", "new york state",
            "singapore", "australia", "canada", "ireland"
        ]
        if not any(j in text for j in known_jurisdictions):
            score += _add_risk(
                matched_rules,
                reasons,
                recommendations,
                "governing_law_foreign",
                "Unusual or unrecognised jurisdiction",
                2,
                _extract_evidence(text, [r"laws of [a-z\s]+", r"jurisdiction of [a-z\s]+"]),
                "Confirm whether the dispute venue and governing law are operationally acceptable.",
            )
        else:
            _add_positive(
                positive_signals,
                "Recognised jurisdiction",
                _extract_evidence(text, [r"india|england|wales|delaware|singapore|california"]),
            )

    if "regulatory" in text and "required by law" not in text and "court order" not in text:
        score += _add_risk(
            matched_rules,
            reasons,
            recommendations,
            "disclosure_regulatory_broad",
            "Broad regulatory disclosure language",
            1,
            "regulatory",
            "Narrow regulatory disclosure language to required disclosures only.",
        )

    if "return or destroy" in text:
        score += _add_risk(
            matched_rules,
            reasons,
            recommendations,
            "return_destroy",
            "Return or destruction obligation",
            1,
            "return or destroy",
            "Add operational carve-outs for backups, legal archives, or automatically retained records if needed.",
        )

    if "certify in writing" in text:
        score += _add_risk(
            matched_rules,
            reasons,
            recommendations,
            "return_certification",
            "Formal compliance requirement",
            1,
            "certify in writing",
            "Confirm the team can comply with written certification timelines.",
        )

    if "survive termination" in text or "continuing obligations" in text:
        score += _add_risk(
            matched_rules,
            reasons,
            recommendations,
            "survival_obligations",
            "Obligations survive termination",
            2,
            _extract_evidence(text, [r"survive termination", r"continuing obligations"]),
            "Check which obligations survive and whether the survival period is clearly limited.",
        )

    if "injunctive relief" in text or "irreparable harm" in text:
        score += _add_risk(
            matched_rules,
            reasons,
            recommendations,
            "remedy_injunctive_relief",
            "Injunctive relief clause",
            2,
            _extract_evidence(text, [r"injunctive relief", r"irreparable harm"]),
            "Verify whether court-based injunctive relief is acceptable alongside any arbitration clause.",
        )

    if "sole discretion" in text:
        score += _add_risk(
            matched_rules,
            reasons,
            recommendations,
            "control_sole_discretion",
            "Unilateral control",
            2,
            "sole discretion",
            "Replace sole-discretion rights with objective standards or mutual approval where possible.",
        )

    if "receiving party shall" in text and "disclosing party shall" not in text:
        score += _add_risk(
            matched_rules,
            reasons,
            recommendations,
            "one_sided_receiving_party",
            "One-sided obligation",
            2,
            "receiving party shall",
            "Consider adding balanced obligations on both parties or clarifying the clause is intentionally one-way.",
        )
    elif "receiving party shall" in text and "disclosing party shall" in text:
        _add_positive(
            positive_signals,
            "Mutual obligations present",
            "receiving party shall / disclosing party shall",
        )

    if "transfer of ownership" in text and "no explicit or implied transfer of ownership" not in text:
        score += _add_risk(
            matched_rules,
            reasons,
            recommendations,
            "ip_transfer_ownership",
            "Ownership transfer",
            3,
            "transfer of ownership",
            "Confirm whether ownership transfer is intended or whether a limited-use license would suffice.",
        )

    if "royalty-free" in text and "irrevocable" in text:
        score += _add_risk(
            matched_rules,
            reasons,
            recommendations,
            "ip_irrevocable_license",
            "Irrevocable license",
            3,
            _extract_evidence(text, [r"royalty-free", r"irrevocable"]),
            "Narrow the scope, duration, or sublicensing rights of any irrevocable license.",
        )

    if category == "force_majeure":
        if "pandemic" not in text:
            score += _add_risk(
                matched_rules,
                reasons,
                recommendations,
                "force_majeure_limited_scope",
                "Limited force majeure scope",
                1,
                "pandemic not found",
                "Consider whether epidemics, pandemics, or government shutdowns should be expressly covered.",
            )
        else:
            _add_positive(
                positive_signals,
                "Pandemic coverage present",
                "pandemic",
            )
    # ── NDA-specific patterns ─────────────────────────────────────────────

    # Broad confidentiality definition
    if re.search(r"any\s+(and\s+all|information|data).{0,50}(confidential|proprietary)", text):
        score += _add_risk(
            matched_rules, reasons, recommendations,
            "broad_definition",
            "Overly broad confidentiality definition",
            2,
            _extract_evidence(text, [r"any and all.{0,30}confidential", r"any information.{0,30}confidential"]),
            "Narrow the definition to specifically identified categories of information.",
        )

    # No time limit on confidentiality obligations
    if ("confidential" in text
            and not re.search(r"\b\d+\s*(year|month)\b|perpetual|indefinite|no\s+expir", text)
            and category in ("confidentiality", "obligations of confidentiality")):
        score += _add_risk(
            matched_rules, reasons, recommendations,
            "no_duration",
            "No confidentiality duration specified",
            2,
            "duration not found",
            "Add an explicit confidentiality period, e.g. 2-3 years from date of disclosure.",
        )

    # One-sided obligations on receiving party
    if (re.search(r"receiving\s+party\s+(shall|must|agrees|will)", text)
            and not re.search(r"disclosing\s+party\s+(shall|must|agrees|will)", text)):
        score += _add_risk(
            matched_rules, reasons, recommendations,
            "one_sided",
            "One-sided obligations on receiving party only",
            1,
            "receiving party shall",
            "Consider whether mutual obligations are appropriate.",
        )

    # Information shared without restriction
    if re.search(r"shared\s+freely|without\s+restriction|freely\s+available|freely\s+shared", text):
        score += _add_risk(
            matched_rules, reasons, recommendations,
            "unrestricted_sharing",
            "Information may be shared without restriction",
            3,
            _extract_evidence(text, [r"shared freely", r"without restriction", r"freely available"]),
            "Add explicit restrictions on disclosure scope and permitted recipients.",
        )

    # Oral disclosures included
    if re.search(r"\b(oral|verbal)\b.{0,60}(confidential|disclos|information)", text):
        score += _add_risk(
            matched_rules, reasons, recommendations,
            "oral_disclosures",
            "Includes oral disclosures",
            1,
            _extract_evidence(text, [r"oral.{0,30}confidential", r"verbal.{0,30}disclosure"]),
            "Consider requiring oral disclosures to be confirmed in writing within a set period.",
        )

    # Obligations survive termination without limit
    if re.search(r"surviv(e|es|al).{0,30}termination", text) and \
       not re.search(r"\b\d+\s*(year|month)\b", text):
        score += _add_risk(
            matched_rules, reasons, recommendations,
            "survival_unlimited",
            "Survival obligations with no time limit",
            2,
            _extract_evidence(text, [r"surviv.{0,20}termination"]),
            "Define a specific survival period rather than open-ended post-termination obligations.",
        )

    normalized_score = max(score, 0)

    if normalized_score >= 3:
        level = "HIGH"
    elif normalized_score >= 1:
        level = "MEDIUM"
    else:
        level = "LOW"

    if not reasons:
        reasons.append("Standard clause")

    if not recommendations and level == "LOW":
        recommendations.append("No immediate redraft priority, but confirm the clause aligns with your commercial position.")

    return {
        "level": level,
        "score": normalized_score,
        "category": category,
        "reason": "; ".join(reasons),
        "summary": _summarize_clause(level, reasons, positive_signals),
        "matched_rules": matched_rules,
        "positive_signals": positive_signals,
        "recommendations": recommendations,
    }
