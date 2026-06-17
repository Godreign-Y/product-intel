# core/models.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class Edge:


    node_1: str
    node_2: str

    method: str

    score: float

    evidence: Optional[list[str]] = None

    raw_score: Optional[float] = None

    p_value: Optional[float] = None
    
    def __str__(self):

     result = (
        f"{self.node_1} ↔ {self.node_2}"
        f" | {self.method}"
        f" | score={self.score:.3f}"
    )

     if self.raw_score is not None:

        result += (
            f" | raw_score={self.raw_score:.3f}"
        )

     if self.p_value is not None:

        result += (
            f" | p_value={self.p_value:.3f}"
        )

     if self.evidence:

        result += (
            f" | evidence={self.evidence}"
        )

     return result