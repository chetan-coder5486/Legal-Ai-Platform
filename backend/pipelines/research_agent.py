from backend.database.connection import vector_collection
from sentence_transformers import SentenceTransformer

embedder = None

def get_embedder():
    global embedder
    if embedder is None:
        print("Loading Sentence Transformer...")
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
    return embedder

def search_precedents(query: str, top_k: int = 2) -> list:
    """
    Embeds a risky clause and searches for similar legal precedents in Vector DB.
    """
    model = get_embedder()
    query_embedding = model.encode(query).tolist()
    
    try:
        results = vector_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        # Results format: {'ids': [['id1', 'id2']], 'documents': [['doc1', 'doc2']], 'metadatas': [...]}
        if results and 'documents' in results and results['documents']:
            return [
                {"id": results['ids'][0][i], "text": results['documents'][0][i], "metadata": results['metadatas'][0][i]}
                for i in range(len(results['documents'][0]))
            ]
    except Exception as e:
        print(f"Error querying ChromaDB: {e}")
        
    # Mock data if DB is empty for demo purposes
    return [
        {
            "id": "mock_case_1", 
            "text": f"Court limited liability clause in XYZ Corp vs ABC Ltd (2018) because financial cap was ambiguous. Related to query: '{query[:30]}...'",
            "metadata": {"source": "XYZ Corp vs ABC Ltd (2018)", "relevance": "high"}
        }
    ]

def summarize_cases(precedents: list) -> str:
    """
    In a full RAG implementation, this would pass the precedents to an LLM for synthesis.
    """
    if not precedents:
        return "No relevant legal precedents found."
        
    synthesis = "Similar cases found:\n"
    for p in precedents:
        synthesis += f"- {p.get('metadata', {}).get('source', 'Unknown Date')}: Context related to the clause.\n"
    return synthesis
