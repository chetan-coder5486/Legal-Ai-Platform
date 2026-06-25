from backend.services.models import ContextResult


class ContextFormatter:

    def __init__(self, include_clause_ids: bool = True):
        self.include_clause_ids = include_clause_ids
        
    """
    Converts a ContextResult into a structured text representation
    suitable for downstream AI models.
    """

    SEPARATOR = "=" * 70

    def format(self, context: ContextResult) -> str:
        lines = []

        # ==========================
        # TARGET CLAUSE
        # ==========================
        lines.append(self.SEPARATOR)
        lines.append("TARGET CLAUSE")
        lines.append(self.SEPARATOR)
        
        if self.include_clause_ids:
            lines.append(f"Clause ID: {context.target.clause_id}")
        lines.append(f"Heading: {context.target.heading}")
        lines.append("")
        lines.append("Body:")
        lines.append(context.target.text.strip())

        # ==========================
        # EVIDENCE
        # ==========================
        if context.evidence:

            lines.append("")
            lines.append(self.SEPARATOR)
            lines.append("SUPPORTING EVIDENCE")
            lines.append(self.SEPARATOR)

            for i, evidence in enumerate(context.evidence, start=1):

                lines.append(f"Evidence #{i}")

                lines.append(
                    f"Retrieved Because: {', '.join(evidence.reasons)}"
                )

                lines.append(
                    f"Retrieval Score: {evidence.retrieval_score:.3f}"
                )

                lines.append(
                    f"Semantic Score: {evidence.semantic_score:.3f}"
                )

                lines.append(
                    f"Heading: {evidence.node.heading}"
                )

                lines.append("Body:")
                lines.append(evidence.node.text.strip())

                lines.append(self.SEPARATOR)

        else:

            lines.append("")
            lines.append(self.SEPARATOR)
            lines.append("NO SUPPORTING EVIDENCE")
            lines.append(self.SEPARATOR)

        return "\n".join(lines)