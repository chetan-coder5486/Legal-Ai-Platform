import sys
import os

# Ensure backend module can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.pipelines.research_agent import ingest_document, search_precedents
from backend.database.connection import vector_collection

def test_ingestion():
    # 1. Ingest a dummy document
    text = "This is a dummy confidentiality clause for testing the new auto-ingestion vector database system. It features very unique words like AutoIngestX99."
    print("Ingesting document...")
    ingest_document("test_doc.txt", text)

    # 2. Search for the unique word
    print("\nSearching for precedent...")
    results = search_precedents("AutoIngestX99")
    print("\nSearch Results:")
    for r in results:
        print(r)

    # 3. Clean up the DB
    print("\nCleaning up test data...")
    test_matches = vector_collection.get(where={"source": "test_doc.txt"})
    if test_matches and test_matches['ids']:
        vector_collection.delete(ids=test_matches['ids'])
        print("Cleaned up successfully.")
    else:
        print("Could not find test document to delete.")

if __name__ == "__main__":
    test_ingestion()
