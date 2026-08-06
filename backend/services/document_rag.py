import chromadb
from sentence_transformers import SentenceTransformer

from backend.services.llm import answer_question


_EMBEDDER = None


def get_embedder():
    global _EMBEDDER
    if _EMBEDDER is None:
        _EMBEDDER = SentenceTransformer('all-MiniLM-L6-v2')
    return _EMBEDDER


class DocumentRAG:

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path="./chroma_db"
        )
        
        self.embedder = get_embedder()
        
    def create_document(self, document_id: str):
        return self.client.get_or_create_collection(
            name=f"document_{document_id}"
        )
            
    def build_embedding_text(self,clause):
        return f"""     
        Clause ID:
        {clause["id"]}
        
        Heading:
        {clause.get("heading","")}

        Clause Type:
        {clause["type"]}

        Risk:
        {clause["risk_level"]}

        Summary:
        {clause["risk_summary"]}
            
        Clause:
        {clause["clause_text"]}
        """.strip()
        
    def delete_document(self, document_id: str):
        try:
            self.client.delete_collection(
                name=f"document_{document_id}"
            )
        except Exception:
            pass
        
    def get_collection(self, document_id: str):
        return self.client.get_collection(
            name=f"document_{document_id}"
        )
        
    def ingest(
        self,
        document_id: str,
        analyzed_clauses: list[dict]
    ):
        self.delete_document(document_id)
        collection = self.create_document(document_id)

        ids = []
        documents = []
        metadatas = []
        embeddings = []

        for clause in analyzed_clauses:

            document = self.build_embedding_text(clause)

            metadata = {
                "clause_id": str(clause["id"]),
                "heading": clause.get("heading", ""),
                "type": clause["type"],
                "risk_level": clause["risk_level"],
                "confidence": float(clause["confidence"]),
            }

            embedding = self.embedder.encode(document).tolist()

            ids.append(f"{document_id}_{clause['id']}")
            documents.append(document)
            metadatas.append(metadata)
            embeddings.append(embedding)

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        return {
            "document_id": document_id,
            "clauses": len(ids),
        }


    def search(
        self,
        document_id: str,
        query: str,
        top_k: int = 5,
        exclude_clause_id: str | None = None,
    ):

        try:
            collection = self.get_collection(document_id)
        except Exception:
            return []

        query_embedding = self.embedder.encode(
            query,
            convert_to_numpy=True
        ).tolist()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k + 1 if exclude_clause_id else top_k,
        )

        matches = []

        for i in range(len(results["ids"][0])):
            match = {
                "id": results["ids"][0][i],
                "distance": results["distances"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
            }

            if exclude_clause_id and match["metadata"].get("clause_id") == exclude_clause_id:
                continue

            matches.append(match)

            if len(matches) >= top_k:
                break

        return matches
    
    def ask(
        self,
        document_id: str,
        question: str,
        top_k: int = 5,
    ):
        matches = self.search(
            document_id=document_id,
            query=question,
            top_k=top_k,
        )

        context = []

        for match in matches:
            doc = match["document"]
            meta = match["metadata"]

            context.append(
                f"""
                Clause {meta['clause_id']}
                Heading: {meta['heading']}
                Type: {meta['type']}
                Risk: {meta['risk_level']}

                {doc}
                """.strip()
            )

        context_text = "\n\n------------------\n\n".join(context)

        answer = answer_question(
            question=question,
            context=context_text,
        )

        return {
            "answer": answer,
            "context": context,
            "sources": matches,
        }
    
    