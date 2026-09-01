from app.schemas.query import (
    QueryResponse,
    EvidenceResponse,
)

from app.services.query_processor import QueryProcessor
from app.services.retriever import Retriever
from app.services.answer_generator import AnswerGenerator
from app.services.semantic_evaluator import (
    SemanticEvaluator,
    SupportLabel,
)
from app.services.confidence import ConfidenceCalculator
from app.services.discrepancy_detector import DiscrepancyDetector


def process_query(question: str) -> QueryResponse:
    """
    Process a user question through the ClarifyAI pipeline.

    Service-layer contract:

        Input:
            question: normalized/validated question text

        Output:
            QueryResponse containing the generated answer,
            confidence, evidence, contradictions,
            discrepancies, and final status.

    The service does not receive FastAPI request objects.
    HTTP/API concerns remain in the route layer.
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
    # 5. Verify the generated answer against evidence
    #
    # SemanticEvaluator internally treats:
    #
    #   evidence = premise
    #   answer   = hypothesis
    #
    # and returns:
    #
    #   ENTAILMENT
    #   NEUTRAL
    #   CONTRADICTION
    # =========================================================

    evaluator = SemanticEvaluator()

    verification_results = [
        evaluator.evaluate(
            answer,
            item.content,
        )
        for item in evidence
    ]

    # =========================================================
    # 6. Calculate confidence
    # =========================================================

    confidence = ConfidenceCalculator.calculate(
        evidence,
        verification_results,
    )

    # =========================================================
    # 7. Detect discrepancies between independent sources
    #
    # This is deliberately separate from answer/evidence
    # contradiction detection.
    # =========================================================

    discrepancy_detector = DiscrepancyDetector()

    discrepancies = discrepancy_detector.detect(
        processed_question,
        evidence,
    )

    # =========================================================
    # 8. Identify evidence that contradicts the answer
    #
    # This is answer-vs-evidence contradiction detection.
    # =========================================================

    contradictions = [
        item.content
        for item, result in zip(
            evidence,
            verification_results,
        )
        if result == SupportLabel.CONTRADICTION
    ]

    # =========================================================
    # 9. Determine final answer reliability
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
            "that contradicts the generated answer."
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
    # 10. Convert internal Evidence objects into API response
    #     objects.
    #
    # The API should not expose internal service/model objects
    # directly.
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
    # 11. Construct the API response
    # =========================================================

    return QueryResponse(
        answer=answer,
        confidence=confidence,
        evidence=evidence_response,
        contradictions=contradictions,
        discrepancies=discrepancies,
        status=status,
        warning=warning,
    )