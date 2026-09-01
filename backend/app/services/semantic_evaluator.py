from enum import Enum

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class SupportLabel(str, Enum):
    """Possible relationships between a claim and evidence."""

    ENTAILMENT = "entailment"
    NEUTRAL = "neutral"
    CONTRADICTION = "contradiction"


class SemanticEvaluator:
    """Evaluates the relationship between a claim and evidence using BART-MNLI."""

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
        Evaluate the relationship between evidence and claim.

        In the NLI formulation:
        - evidence is the premise
        - claim is the hypothesis
        """

        # Tokenize evidence and claim as an explicit
        # premise-hypothesis pair.
        inputs = self.tokenizer(
            evidence,
            claim,
            return_tensors="pt",
            truncation=True,
        )

        # Run BART-MNLI on the encoded premise-hypothesis pair.
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Select the class with the highest model logit.
        predicted_class = outputs.logits.argmax(dim=-1).item()

        # facebook/bart-large-mnli maps:
        # 0 -> contradiction
        # 1 -> neutral
        # 2 -> entailment
        label = self.model.config.id2label[predicted_class].lower()

        if label == "entailment":
            return SupportLabel.ENTAILMENT

        if label == "contradiction":
            return SupportLabel.CONTRADICTION

        return SupportLabel.NEUTRAL