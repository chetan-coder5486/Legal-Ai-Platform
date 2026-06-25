from backend.services.clause_graph import ClauseGraph
from backend.services.models import ContextResult, RetrievalResult


class ContextBuilder:

    def __init__(self, graph: ClauseGraph):
        self.graph = graph
        
    def build_context(
    self,
    clause_id: str,
    top_k: int = 3
    ) -> ContextResult:

        target = self.graph.get_node(clause_id)

        evidence: dict[str, RetrievalResult] = {}

        def add_evidence(
            cid: str,
            reason: str,
            semantic_score: float = 0.0
        ):

            # Never add target clause to evidence
            if cid == clause_id:
                return

            if cid not in self.graph.node_lookup:
                return

            if cid not in evidence:

                evidence[cid] = RetrievalResult(
                    node=self.graph.get_node(cid)
                )

            evidence[cid].reasons.append(reason)

            evidence[cid].semantic_score = max(
                evidence[cid].semantic_score,
                semantic_score
            )

        # Parent
        if target.parent_id:
            add_evidence(
                target.parent_id,
                "parent"
            )

        # Children
        for child in target.children:
            add_evidence(
                child,
                "child"
            )

        # References
        for ref in target.references:
            add_evidence(
                ref,
                "reference"
            )

        # Semantic retrieval
        related = self.graph.find_related_clauses(
            clause_id,
            top_k=top_k
        )

        for cid, score in related:

            add_evidence(
                cid,
                "semantic",
                score
            )

        # Compute final score
        for result in evidence.values():

            score = result.semantic_score

            if "reference" in result.reasons:
                score += 1.0

            if "parent" in result.reasons:
                score += 0.4

            if "child" in result.reasons:
                score += 0.4

            result.retrieval_score = score

        ranked_evidence = sorted(
            evidence.values(),
            key=lambda x: x.retrieval_score,
            reverse=True
        )

        return ContextResult(
            target=target,
            evidence=ranked_evidence
        )
                
                