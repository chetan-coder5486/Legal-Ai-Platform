import sys
sys.path.append("c:/Users/ap080/OneDrive/Desktop/Legal-Ai-Platform")

from backend.services.orchestrator import route_document
from backend.services.parsers import parse_document
import json

with open("c:/Users/ap080/OneDrive/Desktop/Legal-Ai-Platform/Sample_Employment_Contract.pdf", "rb") as f:
    file_bytes = f.read()

text = parse_document("Sample_Employment_Contract.pdf", file_bytes)

print("Text parsed. Routing document...")
result = route_document(text, "analyze_contract")
print("Route document success! Total clauses:", result.get("contract_analysis", {}).get("total_clauses_analyzed"))
