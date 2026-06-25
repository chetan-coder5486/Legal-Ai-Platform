from sentence_transformers import SentenceTransformer
from sentence_transformers import util
from backend.services.models import ClauseNode, RetrievalResult, ContextResult


class ClauseGraph:

    def __init__(self, nodes: list[ClauseNode]):

        self.nodes = nodes

        self.node_lookup = {
            node.clause_id: node
            for node in nodes
        }

        self.embeddings = {}

        self.model = None

    def get_model(self):

        if self.model is None:
            self.model = SentenceTransformer(
                "all-MiniLM-L6-v2"
            )

        return self.model

    def build_embeddings(self):

        model = self.get_model()

        texts = [
            f"{node.heading}\n{node.text}"
            for node in self.nodes
        ]

        embeddings = model.encode(
            texts,
            convert_to_tensor=True,
            show_progress_bar=True
        )

        for node, emb in zip(self.nodes, embeddings):
            self.embeddings[node.clause_id] = emb

    def similarity(
        self,
        clause_a: str,
        clause_b: str
    ) -> float:

        emb_a = self.embeddings[clause_a]
        emb_b = self.embeddings[clause_b]

        return util.cos_sim(
            emb_a,
            emb_b
        ).item()

    def get_node(
        self,
        clause_id: str
    ) -> ClauseNode:

        return self.node_lookup[clause_id]

    def get_children(
        self,
        clause_id: str
    ) -> list[ClauseNode]:

        node = self.get_node(clause_id)

        return [
            self.get_node(child_id)
            for child_id in node.children
        ]

    def get_referenced_nodes(
        self,
        clause_id: str
    ) -> list[ClauseNode]:

        node = self.get_node(clause_id)

        return [
            self.get_node(ref)
            for ref in node.references
            if ref in self.node_lookup
        ]

    def find_related_clauses(
        self,
        clause_id: str,
        top_k: int = 3
    ):

        target_embedding = self.embeddings[clause_id]

        scores = []

        for candidate_id, emb in self.embeddings.items():

            if candidate_id == clause_id:
                continue

            score = util.cos_sim(
                target_embedding,
                emb
            ).item()

            scores.append(
                (
                    candidate_id,
                    score
                )
            )

        scores.sort(
            key=lambda x: x[1],
            reverse=True
        )

        return scores[:top_k]
    
    def get_parent(self, clause_id):

        node = self.get_node(clause_id)

        if not node.parent_id:
            return None

        return self.get_node(node.parent_id)

    