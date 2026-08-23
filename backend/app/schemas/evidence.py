from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """
    Represents a single piece of information retrieved from a source.

    ClarifyAI will use evidence as the foundation for:
    - answer generation
    - semantic verification
    - contradiction detection
    - confidence scoring
    - source verification
    """

    # The actual piece of text from the source.
    content: str = Field(
        ...,
        min_length=1,
        description="Relevant text extracted from the source.",
    )

    # Name of the source.
    source_name: str = Field(
        ...,
        min_length=1,
        description="Name of the information source.",
    )

    # URL of the original source.
    source_url: str | None = Field(
        default=None,
        description="Original URL of the source.",
    )

    # How closely the evidence matches the question.
    relevance_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Relevance score between 0 and 1.",
    )

    # How trustworthy the source is.
    source_quality: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Source quality score between 0 and 1.",
    )