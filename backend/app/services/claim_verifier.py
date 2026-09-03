from dataclasses import dataclass

from app.schemas.evidence import Evidence
from app.services.semantic_evaluator import (
    SemanticEvaluator,
    SupportLabel,
)


@dataclass
class ClaimVerificationResult:
    """Result of verifying one claim against one evidence item."""

    claim: str
    evidence: Evidence
    label: SupportLabel
    entailment_probability: float
    neutral_probability: float
    contradiction_probability: float


class ClaimVerifier:
    """Verifies individual answer claims against retrieved evidence."""

    def __init__(self):
        # Reuse the semantic evaluator for every claim/evidence pair.
        self.evaluator = SemanticEvaluator()

    def verify(
        self,
        claims: list[str],
        evidence: list[Evidence],
    ) -> list[ClaimVerificationResult]:
        """
        Verify every claim against every retrieved evidence item.

        Each claim/evidence pair receives an independent NLI result
        together with the model's class probabilities.
        """

        results = []

        for claim in claims:
            for item in evidence:
                evaluation = self.evaluator.evaluate_with_scores(
                    claim,
                    item.content,
                )

                results.append(
                    ClaimVerificationResult(
                        claim=claim,
                        evidence=item,
                        label=evaluation.label,
                        entailment_probability=(
                            evaluation.entailment_probability
                        ),
                        neutral_probability=(
                            evaluation.neutral_probability
                        ),
                        contradiction_probability=(
                            evaluation.contradiction_probability
                        ),
                    )
                )

        return results