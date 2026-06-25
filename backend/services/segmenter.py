import re
from backend.services.models import ClauseNode
from backend.services.clause_graph import ClauseGraph
from backend.services.context_builder import ContextBuilder

#parse_structure function to parse the structure of a contract and return a list of ClauseNode objects

CLAUSE_PATTERN = re.compile(
    r'(?m)^(\d+(?:\.\d+)*)\.?\s+([^\n]+)'
)

REF_PATTERN = re.compile(
    r'(?:section|clause)\s+(\d+(?:\.\d+)*)',
    re.IGNORECASE
)

def extract_references(text):
    return REF_PATTERN.findall(text)

def get_level(clause_id: str) -> int:
    return len(clause_id.split("."))


def get_parent_id(clause_id: str):
    parts = clause_id.split(".")

    if len(parts) == 1:
        return None

    return ".".join(parts[:-1])


def extract_references(text):
    return REF_PATTERN.findall(text)


def enrich_nodes(nodes):
    for node in nodes:
        node.references = extract_references(node.text)
    
    for node in nodes:
        node.children = [
            n.clause_id
            for n in nodes
            if n.parent_id == node.clause_id
        ]
    
def parse_structure(text: str):

    matches = list(CLAUSE_PATTERN.finditer(text))

    nodes = []

    for i, match in enumerate(matches):

        clause_id = match.group(1)

        heading = match.group(2).strip()

        start = match.start()

        if i < len(matches) - 1:
            end = matches[i + 1].start()
        else:
            end = len(text)

        clause_block = text[start:end].strip()

        body = clause_block.split("\n", 1)

        if len(body) > 1:
            clause_text = body[1].strip()
        else:
            clause_text = ""

        node = ClauseNode(
            clause_id=clause_id,
            heading=heading,
            text=clause_text,
            level=get_level(clause_id),
            parent_id=get_parent_id(clause_id),
            start_pos=start,
            end_pos=end
        )

        nodes.append(node)
        
    enrich_nodes(nodes)
    
    return nodes

