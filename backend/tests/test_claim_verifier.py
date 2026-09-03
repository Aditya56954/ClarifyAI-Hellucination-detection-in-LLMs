from unittest.mock import patch

from app.schemas.evidence import Evidence
from app.services.claim_verifier import ClaimVerifier
from app.services.semantic_evaluator import SupportLabel


def make_evidence(
    content: str,
    source_name: str = "Test Source",
) -> Evidence:
    return Evidence(
        content=content,
        source_name=source_name,
        source_url="https://example.com",
        relevance_score=0.9,
        source_quality=0.9,
    )


def test_verify_claim_against_evidence():
    evidence = [
        make_evidence(
            "Canberra is the capital of Australia."
        )
    ]

    with patch(
        "app.services.claim_verifier.SemanticEvaluator.evaluate",
        return_value=SupportLabel.ENTAILMENT,
    ):
        verifier = ClaimVerifier()

        results = verifier.verify(
            ["Canberra is the capital of Australia."],
            evidence,
        )

    assert len(results) == 1
    assert results[0].claim == (
        "Canberra is the capital of Australia."
    )
    assert results[0].evidence.content == (
        "Canberra is the capital of Australia."
    )
    assert results[0].label == SupportLabel.ENTAILMENT


def test_verify_multiple_claims_against_multiple_evidence():
    evidence = [
        make_evidence(
            "Canberra is the capital of Australia.",
            "Source A",
        ),
        make_evidence(
            "Australia is located in the Southern Hemisphere.",
            "Source B",
        ),
    ]

    with patch(
        "app.services.claim_verifier.SemanticEvaluator.evaluate",
        return_value=SupportLabel.ENTAILMENT,
    ):
        verifier = ClaimVerifier()

        results = verifier.verify(
            [
                "Canberra is the capital of Australia.",
                "Australia is located in the Southern Hemisphere.",
            ],
            evidence,
        )

    assert len(results) == 4


def test_verify_returns_contradiction():
    evidence = [
        make_evidence(
            "Sydney is the capital of Australia."
        )
    ]

    with patch(
        "app.services.claim_verifier.SemanticEvaluator.evaluate",
        return_value=SupportLabel.CONTRADICTION,
    ):
        verifier = ClaimVerifier()

        results = verifier.verify(
            ["Canberra is the capital of Australia."],
            evidence,
        )

    assert len(results) == 1
    assert results[0].label == SupportLabel.CONTRADICTION


def test_verify_empty_claims():
    evidence = [
        make_evidence(
            "Canberra is the capital of Australia."
        )
    ]

    with patch(
        "app.services.claim_verifier.SemanticEvaluator.evaluate",
    ) as evaluate:
        verifier = ClaimVerifier()

        results = verifier.verify(
            [],
            evidence,
        )

    assert results == []
    evaluate.assert_not_called()


def test_verify_empty_evidence():
    with patch(
        "app.services.claim_verifier.SemanticEvaluator.evaluate",
    ) as evaluate:
        verifier = ClaimVerifier()

        results = verifier.verify(
            ["Canberra is the capital of Australia."],
            [],
        )

    assert results == []
    evaluate.assert_not_called()