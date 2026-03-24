from transformers import pipeline
from backend.services.risk_engine import assess_risk

classifier = None

def get_classifier():
    global classifier
    if classifier is None:
        print("Loading Legal-BERT classifier...")
        # For prototype, we'll use a zero-shot classifier or a specific legal-bert model.
        # Since fine-tuning legal-bert for clause classification takes time, 
        # let's use a general zero-shot classification with legal labels for now.
        classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    return classifier

def segment_clauses(text: str) -> list:
    \"\"\"
    Basic segmentation of a contract into clauses.
    In reality, requires regex for numbering (e.g., 1.1, Article II) or NLP sentence splitting.
    \"\"\"
    # Naive split by double newline for now
    raw_clauses = text.split("\n\n")
    return [c.strip() for c in raw_clauses if len(c.strip()) > 20]

def run_contract_analysis(text: str) -> dict:
    \"\"\"
    Run the Contract Analysis pipeline.
    Segments clauses -> Classifies them -> Runs through Risk Engine -> Aggregates results
    \"\"\"
    clauses = segment_clauses(text)
    cls_model = get_classifier()
    
    labels = ["Termination", "Liability", "Confidentiality", "Payment", "Warranties", "Governing Law"]
    
    analyzed_clauses = []
    
    # Just analyze the first 10 clauses to save time for MVP
    for clause in clauses[:10]:
        try:
            result = cls_model(clause, labels, multi_label=False)
            top_label = result['labels'][0]
            confidence = result['scores'][0]
            
            # Run risk engine
            risk_assessment = assess_risk(clause, top_label)
            
            analyzed_clauses.append({
                "clause_text": clause,
                "type": top_label,
                "confidence": confidence,
                "risk_level": risk_assessment["level"],
                "risk_reason": risk_assessment["reason"]
            })
        except Exception as e:
            print(f"Error classifying clause: {e}")
            
    return {
        "pipeline": "Contract Analysis",
        "total_clauses_detected": len(clauses),
        "analyzed_clauses": analyzed_clauses
    }
