import re
from sentence_transformers import SentenceTransformer, util
from backend.services.risk_engine import assess_risk

# -----------------------------
# GLOBALS
# -----------------------------
model = None
label_embeddings = None

labels = [
    "Termination clause about ending agreement",
    "Liability clause about damages and responsibility",
    "Confidentiality clause about data protection",
    "Payment clause about fees and billing",
    "Warranties clause about guarantees",
    "Governing law clause about jurisdiction"
    "Duration clause about time period",
    "Purpose clause about agreement objective",
    "Intellectual property clause about ownership",
    "Exception clause about exclusions",
    "Disclosure clause about sharing information",
    "Obligation clause about responsibilities"
]

CONFIDENCE_THRESHOLD = 0.4


# -----------------------------
# MODEL LOADER
# -----------------------------
def get_model():
    global model, label_embeddings

    if model is None:
        print("Loading Sentence Transformer model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        label_embeddings = model.encode(labels, convert_to_tensor=True)

    return model


# -----------------------------
# OCR NORMALIZATION
# -----------------------------
def normalize_text(text: str) -> str:
    corrections = {
        "Sectlon": "Section",
        "Artlcle": "Article",
        "Deflnltlons": "Definitions",
        "Agreernent": "Agreement",
    }

    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)

    # Force subclauses onto new lines (OCR fix)
    text = re.sub(r'([a-z])\)\s+', r'\n\1) ', text)
    text = re.sub(r'\r', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text


# -----------------------------
# CLAUSE LEVEL DETECTION
# -----------------------------
def get_clause_level(title: str) -> int:
    title = title.lower()

    if re.match(r'^\d+\.', title):
        return 1
    elif re.match(r'^\([a-z]\)', title):
        return 2
    elif title.startswith(("section", "article")):
        return 0
    return 3


# -----------------------------
# CLEAN CLAUSE CONTENT
# -----------------------------
def clean_clause_text(text: str) -> str:
    # remove code noise
    text = re.sub(r'from\s+\w+\s+import\s+\w+', '', text)

    # fix broken OCR words
    text = re.sub(r'(\w)\s+(\w)', r'\1\2', text)  # joins split words

    # fix spacing
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


# -----------------------------
# 🔥 NEW HIERARCHICAL SEGMENTATION
# -----------------------------
def segment_clauses(text: str):
    text = normalize_text(text)

    lines = text.split('\n')

    clauses = []
    current_clause = None

    main_clause_pattern = r'^\d+\.(\s+.*)?$'
    sub_clause_pattern = r'^\(?[a-z]\)'

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # MAIN CLAUSE
        if re.match(main_clause_pattern, line):
            if current_clause:
                current_clause["content"] = clean_clause_text(current_clause["content"])
                clauses.append(current_clause)

            parts = line.split('.', 1)

            title = parts[0] + '.'
            content = parts[1].strip() if len(parts) > 1 else ""

            current_clause = {
                "title": title,
                "content": content + " ",
                "subclauses": [],
                "level": 1
            }

        # SUBCLAUSES
        elif re.match(sub_clause_pattern, line):
            if current_clause:
                current_clause["subclauses"].append(line.strip())

        # NORMAL TEXT
        else:
            if current_clause:
                current_clause["content"] += line + " "

    if current_clause:
        current_clause["content"] = clean_clause_text(current_clause["content"])
        clauses.append(current_clause)

    return clauses


# -----------------------------
# SMART TRUNCATION
# -----------------------------
def smart_truncate(text, max_len=500):
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit('.', 1)[0]


# -----------------------------
# CONFIDENCE LABEL
# -----------------------------
def get_confidence_label(score):
    if score > 0.75:
        return "HIGH"
    elif score > 0.6:
        return "MEDIUM"
    return "LOW"


# -----------------------------
# CLASSIFICATION
# -----------------------------
def classify_clause(clause: str):
    model = get_model()

    clause = smart_truncate(clause)

    clause_emb = model.encode(clause, convert_to_tensor=True)
    scores = util.cos_sim(clause_emb, label_embeddings)[0]

    best_idx = scores.argmax().item()
    confidence = float(scores[best_idx])

    if confidence < CONFIDENCE_THRESHOLD:
        return "Other / Unknown", confidence, "LOW"

    return labels[best_idx], confidence, get_confidence_label(confidence)


# -----------------------------
# 🔥 MAIN PIPELINE (FIXED)
# -----------------------------
def run_contract_analysis(text: str) -> dict:
    clauses = segment_clauses(text)

    analyzed_clauses = []

    for clause_obj in clauses[:12]:

        # 🔥 COMBINE MAIN + SUBCLAUSES
        full_text = clause_obj["content"]

        if clause_obj["subclauses"]:
            full_text += " " + " ".join(clause_obj["subclauses"])

        if len(full_text) < 40:
            continue

        try:
            # Classification
            top_label, confidence, conf_label = classify_clause(full_text)

            # Risk
            try:
                risk_assessment = assess_risk(full_text, top_label)
            except Exception:
                risk_assessment = {
                    "level": "UNKNOWN",
                    "reason": "Risk engine failed"
                }

            analyzed_clauses.append({
                "title": clause_obj["title"],
                "level": clause_obj["level"],

                # 🔥 FIXED OUTPUT
                "clause_text": clause_obj["content"],
                "subclauses": clause_obj["subclauses"],

                "type": top_label,
                "confidence": confidence,
                "confidence_label": conf_label,
                "risk_level": risk_assessment["level"],
                "risk_reason": risk_assessment["reason"]
            })

        except Exception as e:
            print(f"Error processing clause: {e}")

    return {
        "pipeline": "Contract Analysis (Structured + Hierarchical + NLP)",
        "total_clauses_detected": len(clauses),
        "analyzed_clauses": analyzed_clauses
    }