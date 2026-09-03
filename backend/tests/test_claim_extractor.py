from app.services.claim_extractor import ClaimExtractor


def test_extract_basic_claims():
    extractor = ClaimExtractor()

    text = (
        "Canberra is the capital of Australia. "
        "Australia is located in the Southern Hemisphere."
    )

    claims = extractor.extract(text)

    assert claims == [
        "Canberra is the capital of Australia.",
        "Australia is located in the Southern Hemisphere.",
    ]


def test_extract_removes_questions():
    extractor = ClaimExtractor()

    text = (
        "What is the capital of Australia? "
        "Canberra is the capital of Australia."
    )

    claims = extractor.extract(text)

    assert claims == [
        "Canberra is the capital of Australia."
    ]


def test_extract_removes_markdown():
    extractor = ClaimExtractor()

    text = """
    # Answer

    **Canberra is the capital of Australia.**
    """

    claims = extractor.extract(text)

    assert claims == [
        "Canberra is the capital of Australia."
    ]


def test_extract_removes_attribution_prefix():
    extractor = ClaimExtractor()

    text = "According to the report, Canberra is the capital of Australia."

    claims = extractor.extract(text)

    assert claims == [
        "Canberra is the capital of Australia."
    ]


def test_extract_removes_scraper_noise():
    extractor = ClaimExtractor()

    text = "Canberra is the capital of Australia. [source 123]"

    claims = extractor.extract(text)

    assert claims == [
        "Canberra is the capital of Australia."
    ]


def test_extract_deduplicates_claims():
    extractor = ClaimExtractor()

    text = (
        "Canberra is the capital of Australia. "
        "Canberra is the capital of Australia."
    )

    claims = extractor.extract(text)

    assert claims == [
        "Canberra is the capital of Australia."
    ]


def test_extract_short_numeric_claim():
    extractor = ClaimExtractor()

    text = "The population is 1.4 billion."

    claims = extractor.extract(text)

    assert claims == [
        "The population is 1.4 billion."
    ]


def test_extract_empty_text():
    extractor = ClaimExtractor()

    assert extractor.extract("") == []


def test_extract_none():
    extractor = ClaimExtractor()

    assert extractor.extract(None) == []