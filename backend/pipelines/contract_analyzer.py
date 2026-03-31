import re
from sentence_transformers import SentenceTransformer, util
from backend.services.risk_engine import assess_risk

# Global variables (loaded once)
model = None
label_embeddings = None

# Define labels (make them descriptive for better embedding accuracy)
labels = [
    "Termination clause explaining how a contract can be ended or terminated",
    "Liability clause describing legal responsibility damages or losses",
    "Confidentiality clause about protecting sensitive information or data",
    "Payment clause including fees pricing invoices or billing terms",
    "Warranty clause describing guarantees or assurances",
    "Governing law clause specifying jurisdiction or legal authority"
]

# Map long descriptive labels → clean short names for display & risk engine
LABEL_SHORT_NAMES = {
    "Termination clause explaining how a contract can be ended or terminated": "Termination",
    "Liability clause describing legal responsibility damages or losses": "Liability",
    "Confidentiality clause about protecting sensitive information or data": "Confidentiality",
    "Payment clause including fees pricing invoices or billing terms": "Payment",
    "Warranty clause describing guarantees or assurances": "Warranty",
    "Governing law clause specifying jurisdiction or legal authority": "Governing Law"
}


# -----------------------------
# Load model (only once)
# -----------------------------
def get_model():
    global model, label_embeddings

    if model is None:
        print("Loading Sentence Transformer model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')

        # Precompute label embeddings
        label_embeddings = model.encode(labels, convert_to_tensor=True)

    return model


# -----------------------------
# Clause Segmentation
# -----------------------------
def segment_clauses(text: str) -> list:
    """
    Robust clause segmentation for legal text.
    Preserves paragraph boundaries (double-newlines) that parsers.py carefully maintains,
    then splits on numbered clause patterns and uppercase section headers.
    """

    # Step 1: Normalize carriage returns
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Step 2: Normalize 3+ newlines into exactly 2 (preserve paragraph breaks)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Step 3: Join lines that are split mid-sentence (single newline NOT preceded/followed by newline)
    # This fixes broken lines from PDF extraction while preserving paragraph boundaries
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)

    # Step 4: Split on paragraph boundaries, numbered clauses, or uppercase section headers
    pattern = r'\n\n|(?=\s\d+\.\s)|(?=[A-Z][A-Z\s]{5,})'
    clauses = re.split(pattern, text)

    # Step 5: Clean — only keep substantial text blocks (>50 chars)
    clauses = [c.strip() for c in clauses if c and len(c.strip()) > 50]

    return clauses


# -----------------------------
# Clause Classification
# -----------------------------
def classify_clause(clause: str):
    model = get_model()

    # Limit input length for transformer
    clause_input = clause[:500]

    clause_emb = model.encode(clause_input, convert_to_tensor=True)

    scores = util.cos_sim(clause_emb, label_embeddings)[0]

    best_idx = scores.argmax().item()
    full_label = labels[best_idx]
    short_name = LABEL_SHORT_NAMES.get(full_label, full_label)

    return short_name, float(scores[best_idx])


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

    print(f"\n[contract_analyzer] TEXT LENGTH: {len(text)}")
    print(f"[contract_analyzer] TEXT PREVIEW: {repr(text[:200])}")

    clauses = segment_clauses(text)

    print(f"[contract_analyzer] Clauses detected: {len(clauses)}")

    analyzed_clauses = []

    for clause in clauses:
        try:
            # Step 1: Classification
            clause_type, confidence = classify_clause(clause)

            # Step 2: Risk Engine (uses short name like "Termination", "Liability", etc.)
            try:
                risk_assessment = assess_risk(clause, clause_type)
            except Exception:
                risk_assessment = {
                    "level": "UNKNOWN",
                    "reason": "Risk engine failed"
                }

            # Step 3: Store result
            analyzed_clauses.append({
                "clause_text": clause,
                "type": clause_type,
                "confidence": confidence,
                "risk_level": risk_assessment["level"],
                "risk_reason": risk_assessment["reason"]
            })

        except Exception as e:
            print(f"[contract_analyzer] Error processing clause: {e}")

    # Check AFTER the loop completes (not inside)
    if not analyzed_clauses:
        return {
            "error": "No clauses could be processed",
            "hint": "The document may not contain recognizable legal clauses. Check text extraction.",
            "total_clauses_detected": len(clauses)
        }

    return {
        "pipeline": "Contract Analysis (Embedding-Based)",
        "total_clauses_detected": len(clauses),
        "analyzed_clauses": analyzed_clauses
    }