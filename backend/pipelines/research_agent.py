from backend.database.connection import vector_collection
from sentence_transformers import SentenceTransformer

import uuid
import datetime

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
            found_docs = results['documents'][0]
            if found_docs:
                return [
                    {"id": results['ids'][0][i], "text": results['documents'][0][i], "metadata": results['metadatas'][0][i]}
                    for i in range(len(found_docs))
                ]
            else:
                return []  # Database queried successfully but found no documents.
    except Exception as e:
        print(f"Error querying ChromaDB: {e}")
        
    # Mock data only if DB errors out entirely for demo purposes
    return [
        {
            "id": "mock_case_1", 
            "text": f"Court limited liability clause in XYZ Corp vs ABC Ltd (2018) because financial cap was ambiguous. Related to query: '{query[:30]}...'",
            "metadata": {"source": "XYZ Corp vs ABC Ltd (2018)", "relevance": "high"}
        }
    ]

def ingest_document(filename: str, text: str):
    """
    Chunks a document into paragraphs, embeds them, and permanently saves them to the local ChromaDB.
    This acts as our continuous learning pipeline.
    """
    print(f"[{datetime.datetime.now().time()}] Starting background ingestion of {filename} into Vector DB...")
    
    # Simple chunking by paragraph (double newline) or large sentences
    raw_chunks = [c.strip() for c in text.split('\n\n') if len(c.strip()) > 50]
    
    if not raw_chunks:
        print(f"[research_agent] Skipping ingestion for {filename}: No valid chunks found.")
        return
        
    model = get_embedder()
    
    ids = []
    documents = []
    metadatas = []
    
    for idx, chunk in enumerate(raw_chunks):
        chunk_id = f"{filename}_{uuid.uuid4().hex[:8]}_{idx}"
        ids.append(chunk_id)
        documents.append(chunk)
        metadatas.append({
            "source": filename,
            "chunk_index": idx,
            "ingested_at": datetime.datetime.now().isoformat()
        })
        
    print(f"[research_agent] Generating embeddings for {len(raw_chunks)} chunks from {filename}...")
    embeddings = model.encode(documents).tolist()
    
    try:
        vector_collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )
        print(f"[{datetime.datetime.now().time()}] Successfully learned from {filename}. DB updated.")
    except Exception as e:
        print(f"[research_agent] Failed to ingest document into ChromaDB: {e}")

def summarize_cases(precedents: list) -> str:
    """
    In a full RAG implementation, this would pass the precedents to an LLM for synthesis.
    """
    if not precedents:
        return "No relevant legal precedents found in the database."
        
    synthesis = "Similar clauses found in our past documents:\n"
    for p in precedents:
        source = p.get('metadata', {}).get('source', 'Unknown Date')
        snippet = p.get('text', '')[:100] + "..."
        synthesis += f"- {source}: Context related to the clause -> {snippet}\n"
    return synthesis
