import sys
import json
sys.path.append("c:/Users/ap080/OneDrive/Desktop/Legal-Ai-Platform")

from backend.services.parsers import parse_document
from backend.pipelines.contract_analyzer import run_contract_analysis

def run():
    out = {}
    try:
        with open("c:/Users/ap080/OneDrive/Desktop/Legal-Ai-Platform/Sample_Employment_Contract.pdf", "rb") as f:
            file_bytes = f.read()
        
        text = parse_document("Sample_Employment_Contract.pdf", file_bytes)
        out["text_length"] = len(text)
        out["text_preview"] = text[:500]
        
        if len(text) > 0:
            analysis = run_contract_analysis(text)
            out["total_clauses"] = analysis.get("total_clauses_detected", 0)
            out["analyzed_clauses_count"] = analysis.get("total_clauses_analyzed", 0)
            out["analysis"] = analysis
            out["segments"] = text.split("\n\n")[:5] # see first few chunks
    except Exception as e:
        import traceback
        out["error"] = traceback.format_exc()

    with open("c:/Users/ap080/OneDrive/Desktop/Legal-Ai-Platform/test_out.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

if __name__ == "__main__":
    run()
