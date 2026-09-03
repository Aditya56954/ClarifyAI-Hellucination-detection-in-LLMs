from typing import Literal

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for user questions."""

    question: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Question that the user wants ClarifyAI to answer.",
    )


class EvidenceResponse(BaseModel):
    """Evidence returned to the API client."""

    content: str = Field(
        ...,
        min_length=1,
        description="Relevant text extracted from the source.",
    )

    source_name: str = Field(
        ...,
        min_length=1,
        description="Name of the information source.",
    )

    source_url: str | None = Field(
        default=None,
        description="Original URL of the source.",
    )

    relevance_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Relevance score between 0 and 1.",
    )

    source_quality: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Source quality score between 0 and 1.",
    )


class ClaimVerificationResponse(BaseModel):
    """Verification result for one answer claim against one source."""

    claim: str = Field(
        ...,
        min_length=1,
        description="Individual claim extracted from the generated answer.",
    )

    evidence: str = Field(
        ...,
        min_length=1,
        description="Evidence used to verify the claim.",
    )

    source_name: str = Field(
        ...,
        min_length=1,
        description="Source containing the verification evidence.",
    )

    source_url: str | None = Field(
        default=None,
        description="URL of the verification source.",
    )

    label: Literal[
        "entailment",
        "neutral",
        "contradiction",
    ] = Field(
        ...,
        description="NLI relationship between the evidence and claim.",
    )


class QueryResponse(BaseModel):
    """
    Stable API response contract for ClarifyAI queries.

    The response exposes the result of the current verification
    pipeline without exposing internal service implementation
    objects.
    """

    answer: str = Field(
        ...,
        description="Generated answer.",
    )

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Estimated answer confidence between 0 and 1.",
    )

    evidence: list[EvidenceResponse] = Field(
        default_factory=list,
        description="Evidence used by the answer pipeline.",
    )

    # Claim-level verification results.
    claim_verifications: list[ClaimVerificationResponse] = Field(
        default_factory=list,
        description="Individual claim-to-evidence verification results.",
    )

    # Semantic contradictions between the generated answer
    # and retrieved evidence.
    contradictions: list[str] = Field(
        default_factory=list,
        description=(
            "Evidence statements that contradict the generated answer."
        ),
    )

    # Disagreements between different retrieved sources.
    discrepancies: list[str] = Field(
        default_factory=list,
        description=(
            "Cross-source factual discrepancies detected during retrieval."
        ),
    )

    # Current answer-level reliability classification.
    status: Literal[
        "reliable",
        "moderate",
        "uncertain",
        "conflicting",
    ] = Field(
        default="uncertain",
        description="Current answer reliability classification.",
    )

    # Explanation shown when the answer requires caution.
    warning: str | None = Field(
        default=None,
        description="Optional explanation associated with the answer status.",
    )