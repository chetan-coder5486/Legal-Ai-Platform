import re
from sentence_transformers import SentenceTransformer, util
from backend.services.risk_engine import assess_risk

model = None
label_embeddings = None

# ─── NDA-Specific Labels ───────────────────────────────────────────────────
labels = [
    "Definition of confidential information clause",
    "Obligations of confidentiality and non-disclosure clause",
    "Permitted disclosures and exceptions clause",
    "Term and duration of agreement clause",
    "Termination of agreement clause",
    "Return or destruction of confidential information clause",
    "Governing law and jurisdiction clause",
    "Dispute resolution and arbitration clause",
    "Remedies and injunctive relief clause",
    "Intellectual property ownership clause",
    "No license or rights granted clause",
    "Entire agreement and amendments clause",
    "Severability clause",
    "Notices and communications clause",
    "Parties and recitals clause",
]

# ─── Patterns that identify NON-clause content to skip ────────────────────
SKIP_PATTERNS = re.compile(
    r"^("
    r"this\s+(confidentiality|non.disclosure|nda|agreement)\s+"  # preamble
    r"|this\s+agreement\s+is\s+made"                             # opening line
    r"|between\s+.{0,80}(party|parties)"                        # party intro
    r"|hereinafter\s+referred"                                   # party description
    r"|whereas"                                                  # recital opener
    r"|now[\s,]+therefore"                                       # recital closer
    r"|in\s+witness\s+whereof"                                   # signature block
    r"|signed\s+by|executed\s+by|authorized\s+signatory"        # signature
    r"|name\s*:|title\s*:|date\s*:|signature\s*:"               # signature fields
    r"|note\s*:"                                                  # notes like (Note: To be signed...)
    r"|\(note"                                                    # (Note: ...)
    r"|to\s+be\s+duly\s+signed"                                  # signature instructions
    r"|key\s+managerial"                                         # KMP references
    r")",
    re.IGNORECASE
)

# Lettered recitals like "A. Company is engaged..." — background facts not clauses
RECITAL_PATTERN = re.compile(r"^[A-E]\.\s+\S", re.MULTILINE)


def get_model():
    global model, label_embeddings
    if model is None:
        print("[classifier] Loading Sentence Transformer model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        label_embeddings = model.encode(labels, convert_to_tensor=True)
    return model


# ─── Clause Segmentation ───────────────────────────────────────────────────

def segment_clauses(text: str) -> list:
    """
    NDA-aware segmenter that:
    - Splits on numbered clauses (1. / 1.1 / 1.1.1)
    - Splits on ALL CAPS headings
    - Skips preamble, recitals, party descriptions, signature blocks
    - Skips lettered background recitals (A. B. C. D.)
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?i)page\s+\d+\s+of\s+\d+", "", text)
    text = re.sub(r"\-\s*\d+\s*\-", "", text)

    # Split into chunks on numbered clause boundaries
    split_pattern = re.compile(
        r"\n\s*(?="
        r"(?:\d+[\.\)]\d*[\.\)]?\s)"        # 1. or 1.1 or 1.1.1
        r"|(?:[A-Z][A-Z\s\-]{4,}\n)"        # ALL CAPS HEADING on its own line
        r")"
    )

    raw_chunks = split_pattern.split(text)

    # Also split on double newlines within chunks
    all_chunks = []
    for chunk in raw_chunks:
        parts = re.split(r"\n{2,}", chunk)
        all_chunks.extend(parts)

    cleaned = []
    for chunk in all_chunks:
        chunk = chunk.strip()

        # Too short to be a real clause
        if len(chunk) < 60:
            continue

        # Skip preamble / recitals / signature blocks
        first_line = chunk.split("\n")[0].strip().lower()
        first_line_clean = first_line.lstrip('"\'(–—- ')
        if SKIP_PATTERNS.match(first_line_clean):
            continue

        # Skip lettered recitals (A. B. C. short background facts)
        if RECITAL_PATTERN.match(chunk) and len(chunk) < 400:
            continue

        # Skip if overwhelmingly uppercase (title page / cover)
        upper_ratio = sum(1 for c in chunk if c.isupper()) / max(len(chunk), 1)
        if upper_ratio > 0.55 and len(chunk) < 300:
            continue

        # Skip blank-field-only lines (e.g. "______ a company incorporated...")
        blank_ratio = chunk.count("_") / max(len(chunk), 1)
        if blank_ratio > 0.15:
            continue

        cleaned.append(chunk)

    return cleaned


# ─── Clause Classification ─────────────────────────────────────────────────

def classify_clause(clause: str):
    mdl = get_model()
    clause_input = clause[:600]
    clause_emb = mdl.encode(clause_input, convert_to_tensor=True)
    scores = util.cos_sim(clause_emb, label_embeddings)[0]
    best_idx = scores.argmax().item()
    confidence = float(scores[best_idx])

    if confidence < 0.25:
        return "Unclassified clause", confidence

    return labels[best_idx], confidence


# ─── Main Pipeline ─────────────────────────────────────────────────────────

def run_contract_analysis(text: str) -> dict:
    clauses = segment_clauses(text)
    total_detected = len(clauses)
    analyzed_clauses = []

    for clause in clauses:
        try:
            top_label, confidence = classify_clause(clause)

            try:
                risk = assess_risk(clause, top_label)
            except Exception:
                risk = {
                    "level": "UNKNOWN",
                    "reason": "Risk engine failed"
                }

            analyzed_clauses.append({
                "clause_text": clause,
                "type": top_label,
                "confidence": round(confidence, 3),
                "risk_level": risk["level"],
                "risk_reason": risk["reason"]
            })

        except Exception as e:
            print(f"[contract_analyzer] Error processing clause: {e}")

    # Overall risk summary
    high = sum(1 for c in analyzed_clauses if c["risk_level"] == "HIGH")
    medium = sum(1 for c in analyzed_clauses if c["risk_level"] == "MEDIUM")
    low = sum(1 for c in analyzed_clauses if c["risk_level"] == "LOW")

    return {
        "pipeline": "NDA Contract Analysis (Embedding-Based)",
        "total_clauses_detected": total_detected,
        "total_clauses_analyzed": len(analyzed_clauses),
        "risk_summary": {
            "HIGH": high,
            "MEDIUM": medium,
            "LOW": low
        },
        "analyzed_clauses": analyzed_clauses
    }