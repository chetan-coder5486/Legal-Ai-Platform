# test_summarizer.py  ← separate file, NOT inside summarizer.py
from summarizer import run_summarization

text = """
This Agreement is entered into as of January 1, 2024, between Acme Corp
and LegalTech Solutions. The Client agrees to pay USD 50,000 within 30 days.
Either party may terminate this Agreement with 30 days written notice.
All shared information shall remain confidential for 5 years.
"""

result = run_summarization(text)

print("STATUS  :", result["status"])
print("SUMMARY :", result["final_summary"])
print("FACTS   :", result["key_facts"])
print("LENGTH  :", result["doc_length"], "chars")