from app.schemas.evidence import Evidence
from app.services.semantic_evaluator import SupportLabel


class ConfidenceCalculator:
    """Calculates confidence from evidence verification."""

    @staticmethod
    def calculate(
        evidence: list[Evidence],
        verification_results: list[SupportLabel],
    ) -> float:

        # Return zero when no evidence exists.
        if not evidence:
            return 0.0

        scores = []

        for item, result in zip(evidence, verification_results):

            # Start with the evidence relevance.
            score = item.relevance_score or 0.0

            # Reward evidence that supports the answer.
            if result == SupportLabel.ENTAILMENT:
                score *= 1.0

            # Reduce confidence for unrelated evidence.
            elif result == SupportLabel.NEUTRAL:
                score *= 0.5

            # Strongly reduce confidence for contradictions.
            elif result == SupportLabel.CONTRADICTION:
                score *= 0.0

            scores.append(score)

        # Return the average support score.
        return round(sum(scores) / len(scores), 2)