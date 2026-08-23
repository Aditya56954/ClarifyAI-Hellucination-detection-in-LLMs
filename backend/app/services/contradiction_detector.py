from app.schemas.evidence import Evidence
from app.services.semantic_evaluator import (
    SemanticEvaluator,
    SupportLabel,
)


class ContradictionDetector:
    """Detects contradictions between retrieved evidence sources."""

    def __init__(self):
        self.evaluator = SemanticEvaluator()

    def detect(
        self,
        evidence: list[Evidence],
    ) -> list[str]:

        contradictions = []

        # Compare every evidence source with every
        # other evidence source.
        for i in range(len(evidence)):
            for j in range(i + 1, len(evidence)):

                first = evidence[i]
                second = evidence[j]

                result = self.evaluator.evaluate(
                    first.content,
                    second.content,
                )

                if result == SupportLabel.CONTRADICTION:
                    contradictions.append(
                        f"{first.source_name} contradicts "
                        f"{second.source_name}"
                    )

        return contradictions