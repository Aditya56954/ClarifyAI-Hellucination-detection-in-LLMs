from app.schemas.query import (
    ClaimVerificationResponse,
    EvidenceResponse,
    QueryResponse,
)

from app.services.answer_generator import AnswerGenerator
from app.services.claim_extractor import ClaimExtractor
from app.services.claim_verifier import ClaimVerifier
from app.services.confidence import ConfidenceCalculator
from app.services.discrepancy_detector import DiscrepancyDetector
from app.services.query_processor import QueryProcessor
from app.services.retriever import Retriever
from app.services.semantic_evaluator import SupportLabel


def process_query(question: str) -> QueryResponse:
    """
    Process a user question through the ClarifyAI pipeline.

    Service-layer contract:

        Input:
            question: normalized/validated question text

        Output:
            QueryResponse containing the generated answer,
            claim-level verification, confidence, evidence,
            contradictions, discrepancies, and final status.
    """

    # =========================================================
    # 1. Normalize the question
    # =========================================================

    processed_question = QueryProcessor.normalize(
        question
    )

    # =========================================================
    # 2. Validate the normalized question
    # =========================================================

    QueryProcessor.validate(
        processed_question
    )

    # =========================================================
    # 3. Retrieve evidence
    # =========================================================

    retriever = Retriever()

    evidence = retriever.retrieve(
        processed_question
    )

    # =========================================================
    # 4. Generate an evidence-grounded answer
    # =========================================================

    answer_generator = AnswerGenerator()

    answer = answer_generator.generate(
        processed_question,
        evidence,
    )

    # =========================================================
    # 5. Extract individual claims from the answer
    # =========================================================

    claim_extractor = ClaimExtractor()

    claims = claim_extractor.extract(
        answer
    )

    # =========================================================
    # 6. Verify each claim against retrieved evidence
    # =========================================================

    claim_verifier = ClaimVerifier()

    claim_results = claim_verifier.verify(
        claims,
        evidence,
    )

    # =========================================================
    # 7. Preserve the existing evidence-level confidence
    #
    # Confidence will be redesigned around claim-level signals
    # in a later phase. For now, reduce the claim results back
    # to one result per evidence item.
    # =========================================================

    verification_results = []

    for item in evidence:
        item_results = [
            result.label
            for result in claim_results
            if result.evidence is item
        ]

        if SupportLabel.ENTAILMENT in item_results:
            verification_results.append(
                SupportLabel.ENTAILMENT
            )

        elif SupportLabel.CONTRADICTION in item_results:
            verification_results.append(
                SupportLabel.CONTRADICTION
            )

        else:
            verification_results.append(
                SupportLabel.NEUTRAL
            )

    # =========================================================
    # 8. Calculate confidence
    # =========================================================

    confidence = ConfidenceCalculator.calculate(
        evidence,
        verification_results,
    )

    # =========================================================
    # 9. Detect discrepancies between independent sources
    # =========================================================

    discrepancy_detector = DiscrepancyDetector()

    discrepancies = discrepancy_detector.detect(
        processed_question,
        evidence,
    )

    # =========================================================
    # 10. Identify evidence that contradicts at least one claim
    # =========================================================

    contradictions = []

    for result in claim_results:
        if result.label != SupportLabel.CONTRADICTION:
            continue

        if result.evidence.content not in contradictions:
            contradictions.append(
                result.evidence.content
            )

    # =========================================================
    # 11. Determine final answer reliability
    # =========================================================

    if not evidence:
        status = "uncertain"
        warning = (
            "No supporting evidence was retrieved for this answer."
        )

    elif contradictions:
        status = "conflicting"
        warning = (
            "The retrieved evidence contains information "
            "that contradicts one or more generated claims."
        )

    elif confidence >= 0.75:
        status = "reliable"
        warning = None

    elif confidence >= 0.50:
        status = "moderate"
        warning = (
            "The answer has moderate supporting evidence "
            "and should be interpreted with some caution."
        )

    else:
        status = "uncertain"
        warning = (
            "The answer could not be verified with "
            "sufficient confidence."
        )

    # =========================================================
    # 12. Convert evidence into API response objects
    # =========================================================

    evidence_response = [
        EvidenceResponse(
            content=item.content,
            source_name=item.source_name,
            source_url=item.source_url,
            relevance_score=item.relevance_score,
            source_quality=item.source_quality,
        )
        for item in evidence
    ]

    # =========================================================
    # 13. Convert claim verification results into API objects
    # =========================================================

    ClaimVerificationResponse(
    claim=result.claim,
    evidence=result.evidence.content,
    source_name=result.evidence.source_name,
    source_url=result.evidence.source_url,
    label=result.label.value,
    entailment_probability=result.entailment_probability,
    neutral_probability=result.neutral_probability,
    contradiction_probability=result.contradiction_probability,
)

    # =========================================================
    # 14. Construct the API response
    # =========================================================

    return QueryResponse(
        answer=answer,
        confidence=confidence,
        evidence=evidence_response,
        claim_verifications=claim_verification_response,
        contradictions=contradictions,
        discrepancies=discrepancies,
        status=status,
        warning=warning,
    )