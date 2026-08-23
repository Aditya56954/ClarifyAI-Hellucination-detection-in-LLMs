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
    """Evidence returned to the client."""

    content: str
    source_name: str
    source_url: str | None = None
    relevance_score: float | None = None
    source_quality: float | None = None


class QueryResponse(BaseModel):
    """Response returned by the query pipeline."""

    answer: str

    confidence: float | None = None

    evidence: list[EvidenceResponse] = Field(
        default_factory=list
    )

    # Semantic contradictions between the generated answer
    # and the retrieved evidence.
    contradictions: list[str] = Field(
        default_factory=list
    )

    # Numerical/factual discrepancies between different
    # evidence sources.
    discrepancies: list[str] = Field(
        default_factory=list
    )

    # Final reliability classification of the answer.
    status: str = "uncertain"

    # Explanation shown when the answer requires caution.
    warning: str | None = None