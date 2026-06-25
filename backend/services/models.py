from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ClauseNode:
    clause_id: str
    heading: str
    text: str

    level: int = 1
    parent_id: Optional[str] = None

    references: list[str] = field(default_factory=list)
    children: list[str] = field(default_factory=list)

    start_pos: int = 0
    end_pos: int = 0
    

@dataclass
class RetrievalResult:
    node: ClauseNode

    reasons: list[str] = field(default_factory=list)

    semantic_score: float = 0.0

    retrieval_score: float = 0.0
    
@dataclass
class ContextResult:
    target: ClauseNode

    evidence: list[RetrievalResult]
    

@dataclass
class ClassificationResult:
    label: str
    confidence: float