from app.schemas.query import (
    QueryRequest,
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


def process_query(query: QueryRequest) -> QueryResponse:
    """Process a user question through the query pipeline."""

    # 1. Normalize the question.
    processed_question = QueryProcessor.normalize(
        query.question
    )

    # 2. Validate the question.
    QueryProcessor.validate(
        processed_question
    )

    # 3. Retrieve evidence.
    retriever = Retriever()

    evidence = retriever.retrieve(
        processed_question
    )

    # 4. Generate answer from evidence.
    answer_generator = AnswerGenerator()

    answer = answer_generator.generate(
        processed_question,
        evidence,
    )

    # 5. Verify generated answer against evidence.
    evaluator = SemanticEvaluator()

    verification_results = [
        evaluator.evaluate(
            answer,
            item.content,
        )
        for item in evidence
    ]

    # 6. Calculate confidence.
    confidence = ConfidenceCalculator.calculate(
        evidence,
        verification_results,
    )

    # 7. Detect discrepancies between sources.
    discrepancy_detector = DiscrepancyDetector()

    discrepancies = discrepancy_detector.detect(
        processed_question,
        evidence,
    )

    # 8. Identify evidence that directly contradicts
    #    the generated answer.
    contradictions = [
        item.content
        for item, result in zip(
            evidence,
            verification_results,
        )
        if result == SupportLabel.CONTRADICTION
    ]

    # ---------------------------------------------------------
    # 9. Determine final answer reliability.
    # ---------------------------------------------------------

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

    # 10. Convert evidence into API response objects.
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

    # 11. Return final response.
    return QueryResponse(
        answer=answer,
        confidence=confidence,
        evidence=evidence_response,
        contradictions=contradictions,
        discrepancies=discrepancies,
        status=status,
        warning=warning,
    )