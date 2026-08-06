from backend.services.clause_graph import ClauseGraph
from backend.services.context_builder import ContextBuilder
from backend.services.segmenter import parse_structure
from backend.services.context_formatter import ContextFormatter
from backend.services.clause_classifier import ClauseClassifier


nodes = parse_structure("""7. Confidentiality

Recipient shall ...

7.1 Confidential Information

what the parties consider...

18. Survival

The obligations under Section 7 survive termination.""")

graph = ClauseGraph(nodes)

graph.build_embeddings()


print(
    graph.similarity(
        "7",
        "7.1"
    )
)

print(
    graph.find_related_clauses(
        "18"
    )
)

builder = ContextBuilder(graph)

context = builder.build_context(clause_id="7.1")

print(
    context.target.clause_id,
    context.target.heading
)

for result in context.evidence:
    print(
        result.node.clause_id,
        result.node.heading,
        result.node.text,
        result.retrieval_score,
        result.reasons
    )
formatter = ContextFormatter() 

classifier = ClauseClassifier(formatter)
classification_result = classifier.classify(context)    

