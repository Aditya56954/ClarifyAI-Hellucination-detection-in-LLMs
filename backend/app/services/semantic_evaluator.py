from enum import Enum

from transformers import pipeline


class SupportLabel(str, Enum):
    """Possible relationships between a claim and evidence."""

    ENTAILMENT = "entailment"
    NEUTRAL = "neutral"
    CONTRADICTION = "contradiction"


class SemanticEvaluator:
    """Evaluates the relationship between a claim and evidence."""

    _classifier = None

    def __init__(self):
        # Load the model only once.
        if SemanticEvaluator._classifier is None:
            SemanticEvaluator._classifier = pipeline(
                "text-classification",
                model="facebook/bart-large-mnli",
            )

        self.classifier = SemanticEvaluator._classifier

    def evaluate(
        self,
        claim: str,
        evidence: str,
    ) -> SupportLabel:

        # Compare evidence with the claim.
        result = self.classifier(
            f"{evidence} </s></s> {claim}"
        )

        # Handle different pipeline response formats.
        if isinstance(result, list):
            result = result[0]

        label = result["label"].lower()

        if label == "entailment":
            return SupportLabel.ENTAILMENT

        if label == "contradiction":
            return SupportLabel.CONTRADICTION

        return SupportLabel.NEUTRAL