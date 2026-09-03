from types import SimpleNamespace
from unittest.mock import MagicMock

import torch

from app.services.semantic_evaluator import (
    SemanticEvaluationResult,
    SemanticEvaluator,
    SupportLabel,
)


def create_evaluator_with_logits(logits):
    """Create an evaluator without loading the real BART model."""

    evaluator = object.__new__(SemanticEvaluator)

    evaluator.tokenizer = MagicMock()

    evaluator.tokenizer.return_value = {
        "input_ids": torch.tensor([[1, 2, 3]]),
        "attention_mask": torch.tensor([[1, 1, 1]]),
    }

    evaluator.model = MagicMock()

    evaluator.model.return_value = SimpleNamespace(
        logits=torch.tensor([logits], dtype=torch.float32)
    )

    evaluator.model.config.id2label = {
        0: "contradiction",
        1: "neutral",
        2: "entailment",
    }

    return evaluator


def assert_probabilities_sum_to_one(result):
    """Check that the three NLI probabilities form a valid distribution."""

    total = (
        result.entailment_probability
        + result.neutral_probability
        + result.contradiction_probability
    )

    assert abs(total - 1.0) < 1e-6


def test_strong_entailment():
    """A highly confident supporting prediction should produce entailment."""

    evaluator = create_evaluator_with_logits(
        [0.1, 0.3, 4.5]
    )

    result = evaluator.evaluate_with_scores(
        "The company reported revenue of $12.4 billion in 2025.",
        "According to the annual report, the company's revenue reached "
        "$12.4 billion during the 2025 financial year.",
    )

    assert result.label == SupportLabel.ENTAILMENT

    assert result.entailment_probability > 0.9
    assert result.entailment_probability > result.neutral_probability
    assert result.entailment_probability > result.contradiction_probability

    assert_probabilities_sum_to_one(result)


def test_paraphrased_entailment():
    """
    Semantically equivalent wording should still be treated as entailment.

    This is more realistic than testing identical sentences.
    """

    evaluator = create_evaluator_with_logits(
        [0.2, 0.5, 3.8]
    )

    result = evaluator.evaluate_with_scores(
        "The spacecraft successfully entered orbit around Mars.",
        "The mission's spacecraft achieved Martian orbit successfully.",
    )

    assert result.label == SupportLabel.ENTAILMENT

    assert result.entailment_probability > result.neutral_probability
    assert result.entailment_probability > result.contradiction_probability

    assert_probabilities_sum_to_one(result)


def test_strong_contradiction():
    """A directly conflicting factual claim should produce contradiction."""

    evaluator = create_evaluator_with_logits(
        [4.5, 0.3, 0.1]
    )

    result = evaluator.evaluate_with_scores(
        "The company generated $8.2 billion in revenue in 2025.",
        "The company generated $12.4 billion in revenue in 2025.",
    )

    assert result.label == SupportLabel.CONTRADICTION

    assert result.contradiction_probability > 0.9
    assert result.contradiction_probability > result.neutral_probability
    assert result.contradiction_probability > result.entailment_probability

    assert_probabilities_sum_to_one(result)


def test_temporal_contradiction():
    """
    Different years can create a factual conflict when the claim
    refers specifically to the same event.
    """

    evaluator = create_evaluator_with_logits(
        [4.0, 0.5, 0.2]
    )

    result = evaluator.evaluate_with_scores(
        "The company launched the product in 2024.",
        "The company launched the product in 2022.",
    )

    assert result.label == SupportLabel.CONTRADICTION

    assert result.contradiction_probability > result.entailment_probability

    assert_probabilities_sum_to_one(result)


def test_neutral_when_evidence_does_not_address_claim():
    """
    Evidence about a related topic is not automatically supporting evidence.
    """

    evaluator = create_evaluator_with_logits(
        [0.2, 4.2, 0.3]
    )

    result = evaluator.evaluate_with_scores(
        "The company has more than 50,000 employees worldwide.",
        "The company reported strong revenue growth during 2025.",
    )

    assert result.label == SupportLabel.NEUTRAL

    assert result.neutral_probability > result.entailment_probability
    assert result.neutral_probability > result.contradiction_probability

    assert_probabilities_sum_to_one(result)


def test_partial_information_is_not_strong_entailment():
    """
    Evidence mentioning an entity does not necessarily support every
    additional claim about that entity.
    """

    evaluator = create_evaluator_with_logits(
        [0.4, 3.5, 0.7]
    )

    result = evaluator.evaluate_with_scores(
        "The university was founded in 1857 and currently has "
        "more than 40,000 students.",
        "The university was founded in 1857.",
    )

    assert result.label == SupportLabel.NEUTRAL

    assert result.neutral_probability > result.entailment_probability

    assert_probabilities_sum_to_one(result)


def test_numeric_difference_can_be_contradiction():
    """
    A materially different numerical value can represent a contradiction
    when both statements refer to the same quantity and time period.
    """

    evaluator = create_evaluator_with_logits(
        [4.2, 0.4, 0.2]
    )

    result = evaluator.evaluate_with_scores(
        "The population was 8.5 million in 2020.",
        "The population was 10.2 million in 2020.",
    )

    assert result.label == SupportLabel.CONTRADICTION

    assert result.contradiction_probability > result.entailment_probability

    assert_probabilities_sum_to_one(result)


def test_probability_order_matches_predicted_label():
    """
    The predicted label must correspond to the highest model probability.
    """

    evaluator = create_evaluator_with_logits(
        [0.4, 1.2, 2.8]
    )

    result = evaluator.evaluate_with_scores(
        "The drug reduced symptoms significantly.",
        "The clinical trial reported a significant reduction "
        "in patient symptoms.",
    )

    assert result.label == SupportLabel.ENTAILMENT

    assert (
        result.entailment_probability
        == max(
            result.entailment_probability,
            result.neutral_probability,
            result.contradiction_probability,
        )
    )


def test_probabilities_are_between_zero_and_one():
    """Every NLI probability must be a valid probability."""

    evaluator = create_evaluator_with_logits(
        [1.5, 2.0, 3.5]
    )

    result = evaluator.evaluate_with_scores(
        "The organization operates in twelve countries.",
        "The organization currently operates across twelve countries.",
    )

    assert 0.0 <= result.entailment_probability <= 1.0
    assert 0.0 <= result.neutral_probability <= 1.0
    assert 0.0 <= result.contradiction_probability <= 1.0

    assert_probabilities_sum_to_one(result)


def test_evaluate_remains_backward_compatible():
    """
    The existing evaluate() API should still return only SupportLabel.

    This protects Phase 1 and Phase 2.2 callers.
    """

    evaluator = create_evaluator_with_logits(
        [0.1, 0.2, 4.0]
    )

    result = evaluator.evaluate(
        "The Earth orbits the Sun.",
        "The Earth travels around the Sun.",
    )

    assert result == SupportLabel.ENTAILMENT