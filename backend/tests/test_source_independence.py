from app.schemas.evidence import Evidence
from app.services.source_independence import (
    SourceIndependenceEvaluator,
    SourceIndependenceStatus,
)


def make_evidence(
    content: str,
    url: str,
) -> Evidence:
    """Create evidence for source independence tests."""

    return Evidence(
        content=content,
        source_name="Test Source",
        source_url=url,
        relevance_score=0.9,
    )


def test_identical_content_is_not_independent():
    evaluator = SourceIndependenceEvaluator()

    first = make_evidence(
        "Apple reported quarterly revenue growth.",
        "https://source-a.com/article",
    )

    second = make_evidence(
        "Apple reported quarterly revenue growth.",
        "https://source-b.com/article",
    )

    result = evaluator.evaluate(
        first,
        second,
    )

    assert result.status == SourceIndependenceStatus.NOT_INDEPENDENT
    assert result.reason == "identical_content"


def test_near_duplicate_content_is_not_independent():
    evaluator = SourceIndependenceEvaluator()

    first = make_evidence(
        (
            "Apple reported that its quarterly revenue increased "
            "significantly during the latest financial quarter. "
            "The company said revenue reached a record level."
        ),
        "https://source-a.com/article",
    )

    second = make_evidence(
        (
            "Apple reported that its quarterly revenue increased "
            "significantly during the latest financial quarter. "
            "The company said revenue reached a record level. "
            "Read more about the results."
        ),
        "https://source-b.com/article",
    )

    result = evaluator.evaluate(
        first,
        second,
    )

    assert result.status == SourceIndependenceStatus.NOT_INDEPENDENT
    assert result.reason == "near_duplicate_content"


def test_independent_sources_with_different_content_are_independent():
    evaluator = SourceIndependenceEvaluator()

    first = make_evidence(
        (
            "Apple reported quarterly revenue growth after strong "
            "demand for its latest products and services."
        ),
        "https://source-a.com/article",
    )

    second = make_evidence(
        (
            "Apple said its quarterly revenue rose as customers "
            "continued purchasing new devices across several markets."
        ),
        "https://source-b.com/article",
    )

    result = evaluator.evaluate(
        first,
        second,
    )

    assert result.status == SourceIndependenceStatus.INDEPENDENT
    assert result.reason == "different_domains_and_content"


def test_same_domain_different_content_is_uncertain():
    evaluator = SourceIndependenceEvaluator()

    first = make_evidence(
        (
            "Apple reported strong quarterly revenue after increased "
            "demand for its latest products."
        ),
        "https://example.com/article-one",
    )

    second = make_evidence(
        (
            "Apple announced a new product launch after its annual "
            "developer conference."
        ),
        "https://example.com/article-two",
    )

    result = evaluator.evaluate(
        first,
        second,
    )

    assert result.status == SourceIndependenceStatus.UNCERTAIN
    assert result.reason == "same_domain_with_different_content"


def test_whitespace_only_first_content_is_uncertain():
    evaluator = SourceIndependenceEvaluator()

    first = make_evidence(
        "   ",
        "https://source-a.com/article",
    )

    second = make_evidence(
        "Apple reported strong quarterly revenue growth.",
        "https://source-b.com/article",
    )

    result = evaluator.evaluate(
        first,
        second,
    )

    assert result.status == SourceIndependenceStatus.UNCERTAIN
    assert result.reason == "insufficient_content"


def test_whitespace_only_second_content_is_uncertain():
    evaluator = SourceIndependenceEvaluator()

    first = make_evidence(
        "Apple reported strong quarterly revenue growth.",
        "https://source-a.com/article",
    )

    second = make_evidence(
        "   ",
        "https://source-b.com/article",
    )

    result = evaluator.evaluate(
        first,
        second,
    )

    assert result.status == SourceIndependenceStatus.UNCERTAIN
    assert result.reason == "insufficient_content"


def test_same_fact_from_different_sources_can_remain_independent():
    evaluator = SourceIndependenceEvaluator()

    first = make_evidence(
        (
            "The company reported revenue of $100 billion during "
            "the latest financial year."
        ),
        "https://source-a.com/article",
    )

    second = make_evidence(
        (
            "According to financial analysts, the company generated "
            "$100 billion in revenue during the latest financial year."
        ),
        "https://source-b.com/report",
    )

    result = evaluator.evaluate(
        first,
        second,
    )

    assert result.status == SourceIndependenceStatus.INDEPENDENT


def test_group_copies_together():
    evaluator = SourceIndependenceEvaluator()

    original = make_evidence(
        (
            "Apple reported that its quarterly revenue increased "
            "significantly during the latest financial quarter. "
            "The company said revenue reached a record level."
        ),
        "https://source-a.com/article",
    )

    copied = make_evidence(
        (
            "Apple reported that its quarterly revenue increased "
            "significantly during the latest financial quarter. "
            "The company said revenue reached a record level. "
            "Read more about the results."
        ),
        "https://source-b.com/article",
    )

    independent = make_evidence(
        (
            "Analysts said Apple experienced strong demand for "
            "its latest products across several markets."
        ),
        "https://source-c.com/report",
    )

    groups = evaluator.group_evidence(
        [
            original,
            copied,
            independent,
        ]
    )

    assert len(groups) == 2

    assert len(groups[0].evidence) == 2
    assert len(groups[1].evidence) == 1


def test_multiple_independent_sources_create_separate_groups():
    evaluator = SourceIndependenceEvaluator()

    evidence = [
        make_evidence(
            (
                "Apple reported strong quarterly revenue after "
                "increased demand for its latest products."
            ),
            "https://source-a.com/article",
        ),
        make_evidence(
            (
                "Analysts observed stronger customer demand for "
                "Apple devices during the latest quarter."
            ),
            "https://source-b.com/report",
        ),
        make_evidence(
            (
                "Apple announced that its services business grew "
                "during the latest financial period."
            ),
            "https://source-c.com/news",
        ),
    ]

    groups = evaluator.group_evidence(evidence)

    assert len(groups) == 3

    assert all(
        len(group.evidence) == 1
        for group in groups
    )


def test_group_ids_are_sequential():
    evaluator = SourceIndependenceEvaluator()

    evidence = [
        make_evidence(
            "Apple reported strong quarterly revenue growth.",
            "https://source-a.com/article",
        ),
        make_evidence(
            "Microsoft announced a new cloud computing service.",
            "https://source-b.com/article",
        ),
    ]

    groups = evaluator.group_evidence(evidence)

    assert [group.group_id for group in groups] == [0, 1]


def test_empty_evidence_returns_no_groups():
    evaluator = SourceIndependenceEvaluator()

    groups = evaluator.group_evidence([])

    assert groups == []