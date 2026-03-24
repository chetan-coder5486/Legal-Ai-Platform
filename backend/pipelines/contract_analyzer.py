import re
from sentence_transformers import SentenceTransformer, util
from backend.services.risk_engine import assess_risk

# Global variables (loaded once)
model = None
label_embeddings = None

# Define labels (make them descriptive for better accuracy)
labels = [
    "Termination clause about ending agreement",
    "Liability clause about damages and responsibility",
    "Confidentiality clause about data protection",
    "Payment clause about fees and billing",
    "Warranties clause about guarantees",
    "Governing law clause about jurisdiction"
]


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
    Robust clause segmentation for messy legal text
    """

    # Step 1: Normalize spacing
    text = re.sub(r'\r', '\n', text)
    text = re.sub(r'\n+', '\n', text)  # collapse multiple newlines

    # Step 2: FIX broken lines (IMPORTANT)
    # Join lines that are split mid-sentence
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)

    # Step 3: Split using clause numbers (1., 2., 3.)
    pattern = r'(?=\s\d+\.\s)'

    clauses = re.split(pattern, text)

    # Step 4: Clean
    clauses = [c.strip() for c in clauses if len(c.strip()) > 50]

    return clauses


# -----------------------------
# Clause Classification
# -----------------------------
def classify_clause(clause: str):
    model = get_model()

    # Limit input length
    clause = clause[:500]

    clause_emb = model.encode(clause, convert_to_tensor=True)

    scores = util.cos_sim(clause_emb, label_embeddings)[0]

    best_idx = scores.argmax().item()

    return labels[best_idx], float(scores[best_idx])


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

    for clause in clauses[:5]:  # limit for speed (MVP)
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
        "pipeline": "Contract Analysis (Embedding-Based)",
        "total_clauses_detected": len(clauses),
        "analyzed_clauses": analyzed_clauses
    }