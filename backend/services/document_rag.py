import chromadb
from sentence_transformers import SentenceTransformer
import re

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
            source = clause.get("heading") or f"Clause {clause['id']}"

            metadata = {
                "source": source,
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

        if exclude_clause_id is not None:
            exclude_clause_id = str(exclude_clause_id)

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
            metadata = results["metadatas"][0][i]
            document = results["documents"][0][i]
            match = {
                "id": results["ids"][0][i],
                "distance": results["distances"][0][i],
                "document": document,
                "text": document,
                "source": metadata.get("source", "This document"),
                "metadata": metadata,
            }

            if exclude_clause_id and str(match["metadata"].get("clause_id")) == exclude_clause_id:
                continue

            matches.append(match)

            if len(matches) >= top_k:
                break

        return matches

    def get_clauses_by_risk(
        self,
        document_id: str,
        risk_level: str,
    ):
        try:
            collection = self.get_collection(document_id)
        except Exception:
            return []

        results = collection.get(where={"risk_level": risk_level})
        matches = []

        ids = results.get("ids", []) or []
        documents = results.get("documents", []) or []
        metadatas = results.get("metadatas", []) or []
        distances = results.get("distances", []) or []

        for i in range(len(ids)):
            metadata = metadatas[i]
            document = documents[i]
            match = {
                "id": ids[i],
                "distance": distances[i] if i < len(distances) else None,
                "document": document,
                "text": document,
                "source": metadata.get("source", "This document"),
                "metadata": metadata,
            }
            matches.append(match)

        return matches

    def _detect_risk_query(self, question: str):
        normalized = (question or "").lower()

        if re.search(r"\b(high|highest)\s+risk\s+clauses?\b|\bhigh[-\s]?risk\s+clauses?\b", normalized):
            return "HIGH"
        if re.search(r"\b(medium|moderate)\s+risk\s+clauses?\b|\bmedium[-\s]?risk\s+clauses?\b", normalized):
            return "MEDIUM"
        if re.search(r"\b(low|lowest)\s+risk\s+clauses?\b|\blow[-\s]?risk\s+clauses?\b", normalized):
            return "LOW"

        return None
    
    def ask(
        self,
        document_id: str,
        question: str,
        top_k: int = 5,
    ):
        risk_level = self._detect_risk_query(question)

        if risk_level:
            matches = self.get_clauses_by_risk(
                document_id=document_id,
                risk_level=risk_level,
            )
        else:
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

        if risk_level and not matches:
            return {
                "answer": f"There are no {risk_level.lower()}-risk clauses in this contract.",
                "context": [],
                "sources": [],
            }

        answer = answer_question(
            question=question,
            context=context_text,
        )

        return {
            "answer": answer,
            "context": context,
            "sources": matches,
        }
    
    