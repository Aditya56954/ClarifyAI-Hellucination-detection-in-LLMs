from app.services.numeric_verifier import (
    NumericVerificationStatus,
    NumericVerifier,
)


def test_identical_numbers_match():
    verifier = NumericVerifier()

    result = verifier.verify(
        "The company generated $12.4 billion in revenue.",
        "The company reported $12.4 billion in revenue.",
    )

    assert result.status == NumericVerificationStatus.MATCH


def test_million_and_billion_are_equivalent():
    verifier = NumericVerifier()

    result = verifier.verify(
        "The company generated $12.4 billion in revenue.",
        "The company generated $12,400 million in revenue.",
    )

    assert result.status == NumericVerificationStatus.MATCH


def test_thousand_and_million_are_equivalent():
    verifier = NumericVerifier()

    result = verifier.verify(
        "The project cost 5 million dollars.",
        "The project cost 5,000 thousand dollars.",
    )

    assert result.status == NumericVerificationStatus.MATCH


def test_different_revenue_is_detected():
    verifier = NumericVerifier()

    result = verifier.verify(
        "The company generated $12.4 billion in revenue.",
        "The company generated $8.2 billion in revenue.",
    )

    assert result.status == NumericVerificationStatus.DIFFERENT


def test_small_approximation_difference_matches():
    verifier = NumericVerifier(
        relative_tolerance=0.02,
    )

    result = verifier.verify(
        "The population is approximately 10 million.",
        "The population is 9.9 million.",
    )

    assert result.status == NumericVerificationStatus.MATCH


def test_large_difference_does_not_match():
    verifier = NumericVerifier(
        relative_tolerance=0.02,
    )

    result = verifier.verify(
        "The population is approximately 10 million.",
        "The population is 8 million.",
    )

    assert result.status == NumericVerificationStatus.DIFFERENT


def test_percentage_values_match():
    verifier = NumericVerifier()

    result = verifier.verify(
        "The unemployment rate was 5%.",
        "The unemployment rate was 5 percent.",
    )

    assert result.status == NumericVerificationStatus.MATCH


def test_percentage_difference_is_detected():
    verifier = NumericVerifier()

    result = verifier.verify(
        "The unemployment rate was 5%.",
        "The unemployment rate was 8%.",
    )

    assert result.status == NumericVerificationStatus.DIFFERENT


def test_percentage_and_currency_are_incompatible():
    verifier = NumericVerifier()

    result = verifier.verify(
        "The company grew by 5%.",
        "The company generated $5 billion.",
    )

    assert result.status == NumericVerificationStatus.INCOMPATIBLE


def test_different_currencies_are_incompatible():
    verifier = NumericVerifier()

    result = verifier.verify(
        "The company generated $5 billion.",
        "The company generated €5 billion.",
    )

    assert result.status == NumericVerificationStatus.INCOMPATIBLE


def test_same_currency_different_values():
    verifier = NumericVerifier()

    result = verifier.verify(
        "The company generated $5 billion.",
        "The company generated $7 billion.",
    )

    assert result.status == NumericVerificationStatus.DIFFERENT


def test_non_numeric_claim_is_not_applicable():
    verifier = NumericVerifier()

    result = verifier.verify(
        "The company operates internationally.",
        "The company operates across several countries.",
    )

    assert result.status == NumericVerificationStatus.NOT_APPLICABLE


def test_claim_without_number_is_not_applicable():
    verifier = NumericVerifier()

    result = verifier.verify(
        "The company has significant revenue.",
        "The company reported $12 billion in revenue.",
    )

    assert result.status == NumericVerificationStatus.NOT_APPLICABLE


def test_empty_text_is_not_applicable():
    verifier = NumericVerifier()

    result = verifier.verify(
        "",
        "The company generated $12 billion.",
    )

    assert result.status == NumericVerificationStatus.NOT_APPLICABLE


def test_comma_separated_number():
    verifier = NumericVerifier()

    result = verifier.verify(
        "The population was 1,500,000.",
        "The population was 1.5 million.",
    )

    assert result.status == NumericVerificationStatus.MATCH


def test_decimal_values_match():
    verifier = NumericVerifier()

    result = verifier.verify(
        "The distance was 12.5 kilometers.",
        "The distance was 12.5 kilometers.",
    )

    assert result.status == NumericVerificationStatus.MATCH


def test_numeric_values_are_extracted():
    verifier = NumericVerifier()

    values = verifier.extract_values(
        "Revenue increased from $8.2 billion to $12.4 billion."
    )

    assert len(values) == 2

    assert values[0].value == 8.2
    assert values[1].value == 12.4

    assert values[0].normalized_value == 8_200_000_000
    assert values[1].normalized_value == 12_400_000_000