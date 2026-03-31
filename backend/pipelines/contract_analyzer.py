import re
from transformers import pipeline as hf_pipeline
from backend.services.risk_engine import assess_risk

# ─── NLI Classifier (lazy-loaded) ─────────────────────────────────────────
_classifier = None

LABELS = [
    "Termination",
    "Liability",
    "Confidentiality",
    "Payment",
    "Warranties",
    "Governing Law",
    "Indemnification",
    "Force Majeure",
    "Intellectual Property",
    "Dispute Resolution",
]


def get_classifier():
    global _classifier
    if _classifier is None:
        print("Loading Zero-Shot NLI model (DeBERTa)...")
        _classifier = hf_pipeline(
            "zero-shot-classification",
            model="MoritzLaurer/deberta-v3-base-zeroshot-v2.0",
        )
    return _classifier


# ─────────────────────────────────────────────────────
# 🔥 KEEP YOUR ORIGINAL SEGMENTATION (NO CHANGE)
# ─────────────────────────────────────────────────────

_HEADING_RE = re.compile(
    r"""
    ^[ \t]*
    (?:
        (?:article|section|clause|schedule|exhibit|annex|recital|part)
            \s+[\w.]+
      | \d+(?:\.\d+)*\.?\s
      | \([a-z]\)\s
      | \([ivxlc]+\)\s
      | [A-Z][A-Z\s]{4,}$
    )
    """,
    re.IGNORECASE | re.MULTILINE | re.VERBOSE,
)

_MIN_CLAUSE_LENGTH = 50


def segment_clauses(text: str) -> list:
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    split_positions = [m.start() for m in _HEADING_RE.finditer(text)]

    if split_positions:
        if split_positions[0] != 0:
            split_positions.insert(0, 0)

        raw_clauses = []
        for i, pos in enumerate(split_positions):
            end = split_positions[i + 1] if i + 1 < len(split_positions) else len(text)
            chunk = text[pos:end].strip()
            if chunk:
                raw_clauses.append(chunk)
    else:
        raw_clauses = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

    merged = []
    for clause in raw_clauses:
        if merged and len(clause) < _MIN_CLAUSE_LENGTH:
            merged[-1] = merged[-1] + "\n\n" + clause
        else:
            merged.append(clause)

    clauses = [c for c in merged if len(c) >= _MIN_CLAUSE_LENGTH]

    return clauses


# ─────────────────────────────────────────────────────
# 🔥 IMPROVED CLASSIFICATION (multi-label)
# ─────────────────────────────────────────────────────

def classify_clause(clause: str):
    clf = get_classifier()

    result = clf(
        clause[:1500],
        candidate_labels=LABELS,
        multi_label=True   # 🔥 IMPORTANT CHANGE
    )

    labels = result["labels"]
    scores = result["scores"]

    # keep meaningful labels only
    filtered = [
        (label, round(score, 4))
        for label, score in zip(labels, scores)
        if score > 0.4
    ]

    if not filtered:
        return [("Other", 0.0)]

    return filtered


# ─────────────────────────────────────────────────────
# 🚀 MAIN PIPELINE
# ─────────────────────────────────────────────────────

def run_contract_analysis(text: str) -> dict:
    """
    FINAL FLOW:
    cleaned_text → segment_clauses → classify → risk
    """

    # 🔥 IMPORTANT: Make sure text is already cleaned BEFORE calling this
    clauses = segment_clauses(text)

    analyzed_clauses = []

    for clause in clauses:
        try:
            # 🔥 Multi-label classification
            classifications = classify_clause(clause)

            top_label = classifications[0][0]
            confidence = classifications[0][1]

            # 🔥 Risk analysis
            try:
                risk = assess_risk(clause, top_label)
            except Exception:
                risk = {
                    "level": "UNKNOWN",
                    "reason": "Risk engine failed"
                }

            analyzed_clauses.append({
                "clause_text": clause,
                "types": classifications,        # 🔥 multiple labels
                "primary_type": top_label,
                "confidence": confidence,
                "risk_level": risk["level"],
                "risk_reason": risk["reason"]
            })

        except Exception as e:
            print(f"Error processing clause: {e}")

    return {
        "pipeline": "Advanced Contract Analysis",
        "total_clauses_detected": len(clauses),
        "analyzed_clauses": analyzed_clauses
    }