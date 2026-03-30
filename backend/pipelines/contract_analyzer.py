import re
from transformers import pipeline as hf_pipeline
from backend.services.risk_engine import assess_risk

# ─── NLI Classifier (lazy-loaded) ─────────────────────────────────────────
_classifier = None

# Short, clear labels work best with NLI — the model infers meaning
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
    """Lazy-load the NLI classifier so the server starts fast."""
    global _classifier
    if _classifier is None:
        print("Loading Zero-Shot NLI model (DeBERTa)...")
        _classifier = hf_pipeline(
            "zero-shot-classification",
            model="MoritzLaurer/deberta-v3-base-zeroshot-v2.0",
        )
    return _classifier


# ─── Clause heading patterns (compiled once) ──────────────────────────────

# Matches lines that look like clause / section headings
_HEADING_RE = re.compile(
    r"""
    ^[ \t]*                                  # optional leading whitespace
    (?:
        (?:article|section|clause|schedule|exhibit|annex|recital|part)
            \s+[\w.]+                        # "Article I", "Section 2.3"
      | \d+(?:\.\d+)*\.?\s                   # "1. ", "1.1 ", "12.3.1 "
      | \([a-z]\)\s                          # "(a) "
      | \([ivxlc]+\)\s                       # "(i) ", "(iv) "
      | [A-Z][A-Z\s]{4,}$                    # ALL CAPS heading (≥5 chars)
    )
    """,
    re.IGNORECASE | re.MULTILINE | re.VERBOSE,
)

# Minimum characters for a clause to survive the final filter
_MIN_CLAUSE_LENGTH = 50


# -----------------------------
# Clause Segmentation
# -----------------------------
def segment_clauses(text: str) -> list:
    """
    Robust, multi-strategy clause segmentation for legal text.

    Strategy order:
      1. Detect heading lines (numbered, titled, ALL CAPS) and split on them.
      2. If no headings found, fall back to splitting on paragraph boundaries
         (double-newline, which clean_text preserves).
      3. Merge tiny fragments (< _MIN_CLAUSE_LENGTH) into the previous clause.
      4. Drop anything still under the minimum length after merging.
    """

    # ── Step 1: normalise line endings (preserve double-newlines!) ────────
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # ── Step 2: try heading-based splitting ───────────────────────────────
    #    Find all positions where a heading line starts.
    split_positions = [m.start() for m in _HEADING_RE.finditer(text)]

    if split_positions:
        # Make sure we capture any preamble before the first heading
        if split_positions[0] != 0:
            split_positions.insert(0, 0)

        raw_clauses = []
        for i, pos in enumerate(split_positions):
            end = split_positions[i + 1] if i + 1 < len(split_positions) else len(text)
            chunk = text[pos:end].strip()
            if chunk:
                raw_clauses.append(chunk)
    else:
        # ── Step 2b: fall back to paragraph-boundary splitting ────────────
        raw_clauses = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

    # ── Step 3: merge tiny fragments into the preceding clause ────────────
    merged: list[str] = []
    for clause in raw_clauses:
        if merged and len(clause) < _MIN_CLAUSE_LENGTH:
            merged[-1] = merged[-1] + "\n\n" + clause
        else:
            merged.append(clause)

    # ── Step 4: final length filter ───────────────────────────────────────
    clauses = [c for c in merged if len(c) >= _MIN_CLAUSE_LENGTH]

    return clauses


# -----------------------------
# Clause Classification (NLI)
# -----------------------------
def classify_clause(clause: str):
    """
    Classify a clause using Zero-Shot Natural Language Inference.
    Returns (label, confidence_score).
    """
    clf = get_classifier()

    # Truncate to model max-token window (~512 tokens ≈ 1500 chars)
    result = clf(clause[:1500], candidate_labels=LABELS, multi_label=False)

    return result["labels"][0], round(result["scores"][0], 4)


# -----------------------------
# Main Pipeline
# -----------------------------
def run_contract_analysis(text: str) -> dict:
    """
    Full pipeline:
    1. Segment clauses
    2. Classify each clause
    3. Run risk engine
    4. Return structured output
    """

    clauses = segment_clauses(text)

    analyzed_clauses = []

    for clause in clauses:  # limit for speed (MVP)
        try:
            # Step 1: Classification
            top_label, confidence = classify_clause(clause)

            # Step 2: Risk Engine
            try:
                risk_assessment = assess_risk(clause, top_label)
            except Exception:
                risk_assessment = {
                    "level": "UNKNOWN",
                    "reason": "Risk engine failed"
                }

            # Step 3: Store result
            analyzed_clauses.append({
                "clause_text": clause,
                "type": top_label,
                "confidence": confidence,
                "risk_level": risk_assessment["level"],
                "risk_reason": risk_assessment["reason"]
            })

        except Exception as e:
            print(f"Error processing clause: {e}")

    return {
        "pipeline": "Contract Analysis (Zero-Shot NLI)",
        "total_clauses_detected": len(clauses),
        "analyzed_clauses": analyzed_clauses
    }