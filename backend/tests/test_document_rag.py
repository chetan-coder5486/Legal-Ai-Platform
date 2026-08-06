from backend.services.document_rag import DocumentRAG

rag = DocumentRAG()

document_id = "766cb0d2-41aa-4921-8479-f40175c67814"

results = rag.search(
    document_id=document_id,
    query="When does confidentiality end?",
    top_k=3,
)

context = rag.ask(
    document_id=document_id,
    question="Who can disclose confidential information?"
)

print(context)

# for r in results:
#     print("=" * 80)
#     print("Clause:", r["metadata"]["clause_id"])
#     print("Type:", r["metadata"]["type"])
#     print("Risk:", r["metadata"]["risk_level"])
#     print("Distance:", r["distance"])
#     print(r["document"][:500])