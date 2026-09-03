from app.schemas.evidence import Evidence
from app.services.evidence_deduplicator import EvidenceDeduplicator


def make_evidence(
    content: str,
    url: str,
) -> Evidence:
    """Create evidence for deduplication tests."""

    return Evidence(
        content=content,
        source_name="Test Source",
        source_url=url,
        relevance_score=0.9,
    )


def test_unique_evidence_is_preserved():
    deduplicator = EvidenceDeduplicator()

    evidence = [
        make_evidence(
            "Canberra is the capital of Australia.",
            "https://example.com/canberra",
        ),
        make_evidence(
            "Sydney is the largest city in Australia.",
            "https://example.com/sydney",
        ),
    ]

    result = deduplicator.deduplicate(evidence)

    assert len(result.unique_evidence) == 2
    assert len(result.duplicate_evidence) == 0


def test_exact_duplicate_url_is_removed():
    deduplicator = EvidenceDeduplicator()

    evidence = [
        make_evidence(
            "Canberra is the capital of Australia.",
            "https://example.com/article",
        ),
        make_evidence(
            "Canberra is the capital of Australia.",
            "https://example.com/article",
        ),
    ]

    result = deduplicator.deduplicate(evidence)

    assert len(result.unique_evidence) == 1
    assert len(result.duplicate_evidence) == 1


def test_trailing_slash_is_normalized():
    deduplicator = EvidenceDeduplicator()

    evidence = [
        make_evidence(
            "Canberra is the capital of Australia.",
            "https://example.com/article/",
        ),
        make_evidence(
            "Canberra is the capital of Australia.",
            "https://example.com/article",
        ),
    ]

    result = deduplicator.deduplicate(evidence)

    assert len(result.unique_evidence) == 1
    assert len(result.duplicate_evidence) == 1


def test_tracking_parameters_are_ignored():
    deduplicator = EvidenceDeduplicator()

    evidence = [
        make_evidence(
            "Canberra is the capital of Australia.",
            "https://example.com/article?utm_source=google",
        ),
        make_evidence(
            "Canberra is the capital of Australia.",
            "https://example.com/article?utm_source=newsletter",
        ),
    ]

    result = deduplicator.deduplicate(evidence)

    assert len(result.unique_evidence) == 1
    assert len(result.duplicate_evidence) == 1


def test_query_parameter_order_is_normalized():
    deduplicator = EvidenceDeduplicator()

    evidence = [
        make_evidence(
            "First article content.",
            "https://example.com/article?a=1&b=2",
        ),
        make_evidence(
            "Second article content.",
            "https://example.com/article?b=2&a=1",
        ),
    ]

    result = deduplicator.deduplicate(evidence)

    assert len(result.unique_evidence) == 1
    assert len(result.duplicate_evidence) == 1


def test_identical_content_from_different_urls_is_removed():
    deduplicator = EvidenceDeduplicator()

    content = "Canberra is the capital of Australia."

    evidence = [
        make_evidence(
            content,
            "https://source-a.com/article",
        ),
        make_evidence(
            content,
            "https://source-b.com/article",
        ),
    ]

    result = deduplicator.deduplicate(evidence)

    assert len(result.unique_evidence) == 1
    assert len(result.duplicate_evidence) == 1


def test_whitespace_differences_are_ignored():
    deduplicator = EvidenceDeduplicator()

    evidence = [
        make_evidence(
            "Canberra is the capital of Australia.",
            "https://source-a.com/article",
        ),
        make_evidence(
            "  Canberra   is the capital of Australia.  ",
            "https://source-b.com/article",
        ),
    ]

    result = deduplicator.deduplicate(evidence)

    assert len(result.unique_evidence) == 1
    assert len(result.duplicate_evidence) == 1


def test_case_differences_are_ignored():
    deduplicator = EvidenceDeduplicator()

    evidence = [
        make_evidence(
            "Canberra is the capital of Australia.",
            "https://source-a.com/article",
        ),
        make_evidence(
            "CANBERRA IS THE CAPITAL OF AUSTRALIA.",
            "https://source-b.com/article",
        ),
    ]

    result = deduplicator.deduplicate(evidence)

    assert len(result.unique_evidence) == 1
    assert len(result.duplicate_evidence) == 1


def test_different_content_from_different_sources_is_preserved():
    deduplicator = EvidenceDeduplicator()

    evidence = [
        make_evidence(
            "Canberra is the capital of Australia.",
            "https://source-a.com/article",
        ),
        make_evidence(
            "Sydney is the largest city in Australia.",
            "https://source-b.com/article",
        ),
    ]

    result = deduplicator.deduplicate(evidence)

    assert len(result.unique_evidence) == 2
    assert len(result.duplicate_evidence) == 0


def test_duplicate_order_is_preserved():
    deduplicator = EvidenceDeduplicator()

    first = make_evidence(
        "First unique article.",
        "https://source-a.com/article",
    )

    duplicate = make_evidence(
        "First unique article.",
        "https://source-b.com/article",
    )

    second = make_evidence(
        "Second unique article.",
        "https://source-c.com/article",
    )

    result = deduplicator.deduplicate(
        [first, duplicate, second]
    )

    assert result.unique_evidence == [first, second]
    assert result.duplicate_evidence == [duplicate]


def test_near_identical_content_is_removed():
    deduplicator = EvidenceDeduplicator()

    evidence = [
        make_evidence(
            (
                "Apple reported that its quarterly revenue increased "
                "significantly during the latest financial quarter. "
                "The company said revenue reached a record level."
            ),
            "https://source-a.com/article",
        ),
        make_evidence(
            (
                "Apple reported that its quarterly revenue increased "
                "significantly during the latest financial quarter. "
                "The company said revenue reached a record level. "
                "Read more about the results."
            ),
            "https://source-b.com/article",
        ),
    ]

    result = deduplicator.deduplicate(evidence)

    assert len(result.unique_evidence) == 1
    assert len(result.duplicate_evidence) == 1


def test_independent_similar_reporting_is_preserved():
    deduplicator = EvidenceDeduplicator()

    evidence = [
        make_evidence(
            (
                "Apple reported quarterly revenue growth after strong "
                "demand for its latest products and services."
            ),
            "https://source-a.com/article",
        ),
        make_evidence(
            (
                "Apple said its quarterly revenue rose as customers "
                "continued purchasing new devices across several markets."
            ),
            "https://source-b.com/article",
        ),
    ]

    result = deduplicator.deduplicate(evidence)

    assert len(result.unique_evidence) == 2
    assert len(result.duplicate_evidence) == 0


def test_short_similar_content_is_not_marked_as_near_duplicate():
    deduplicator = EvidenceDeduplicator()

    evidence = [
        make_evidence(
            "Apple revenue increased this year.",
            "https://source-a.com/article",
        ),
        make_evidence(
            "Apple revenue increased this quarter.",
            "https://source-b.com/article",
        ),
    ]

    result = deduplicator.deduplicate(evidence)

    assert len(result.unique_evidence) == 2
    assert len(result.duplicate_evidence) == 0