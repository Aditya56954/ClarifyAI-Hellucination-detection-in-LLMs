from dataclasses import dataclass
from enum import Enum

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class SupportLabel(str, Enum):
    """Possible relationships between a claim and evidence."""

    ENTAILMENT = "entailment"
    NEUTRAL = "neutral"
    CONTRADICTION = "contradiction"


@dataclass
class SemanticEvaluationResult:
    """NLI result with both the predicted label and class probabilities."""

    label: SupportLabel
    entailment_probability: float
    neutral_probability: float
    contradiction_probability: float


class SemanticEvaluator:
    """Evaluates claim/evidence relationships using BART-MNLI."""

    _tokenizer = None
    _model = None

    def __init__(self):
        # Load the tokenizer and model only once.
        if SemanticEvaluator._tokenizer is None:
            SemanticEvaluator._tokenizer = AutoTokenizer.from_pretrained(
                "facebook/bart-large-mnli"
            )

        if SemanticEvaluator._model is None:
            SemanticEvaluator._model = (
                AutoModelForSequenceClassification.from_pretrained(
                    "facebook/bart-large-mnli"
                )
            )

        self.tokenizer = SemanticEvaluator._tokenizer
        self.model = SemanticEvaluator._model

    def evaluate(
        self,
        claim: str,
        evidence: str,
    ) -> SupportLabel:
        """
        Return only the predicted NLI label.

        This method is intentionally kept backward compatible because
        existing discrepancy and confidence logic depends on SupportLabel.
        """

        result = self.evaluate_with_scores(
            claim,
            evidence,
        )

        return result.label

    def evaluate_with_scores(
        self,
        claim: str,
        evidence: str,
    ) -> SemanticEvaluationResult:
        """
        Evaluate a claim against evidence and retain NLI probabilities.

        In the NLI formulation:
        - evidence is the premise
        - claim is the hypothesis
        """

        # Tokenize evidence and claim as a premise-hypothesis pair.
        inputs = self.tokenizer(
            evidence,
            claim,
            return_tensors="pt",
            truncation=True,
        )

        # Run the NLI model without calculating gradients.
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Convert raw logits into probabilities.
        probabilities = torch.softmax(
            outputs.logits,
            dim=-1,
        )[0]

        # Resolve probabilities using the model's label mapping.
        label_probabilities = {}

        for class_id, probability in enumerate(probabilities):
            label = self.model.config.id2label[class_id].lower()
            label_probabilities[label] = float(probability.item())

        entailment_probability = label_probabilities.get(
            "entailment",
            0.0,
        )

        neutral_probability = label_probabilities.get(
            "neutral",
            0.0,
        )

        contradiction_probability = label_probabilities.get(
            "contradiction",
            0.0,
        )

        # The predicted class is still the class with the highest probability.
        predicted_class = probabilities.argmax().item()

        predicted_label = self.model.config.id2label[
            predicted_class
        ].lower()

        if predicted_label == "entailment":
            label = SupportLabel.ENTAILMENT

        elif predicted_label == "contradiction":
            label = SupportLabel.CONTRADICTION

        else:
            label = SupportLabel.NEUTRAL

        return SemanticEvaluationResult(
            label=label,
            entailment_probability=entailment_probability,
            neutral_probability=neutral_probability,
            contradiction_probability=contradiction_probability,
        )