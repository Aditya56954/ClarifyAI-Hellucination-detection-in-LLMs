from app.services.temporal_verifier import (
    TemporalVerificationStatus,
    TemporalVerifier,
)


def test_same_year_matches():
    verifier = TemporalVerifier()

    result = verifier.verify(
        "The population in 2024 was 1.4 billion.",
        "In 2024, the population was 1.4 billion.",
    )

    assert result.status == TemporalVerificationStatus.MATCH


def test_different_years_are_different_not_contradictory():
    verifier = TemporalVerifier()

    result = verifier.verify(
        "The population in 2024 was 1.4 billion.",
        "The population in 2025 was 1.45 billion.",
    )

    assert result.status == TemporalVerificationStatus.DIFFERENT


def test_no_temporal_information():
    verifier = TemporalVerifier()

    result = verifier.verify(
        "The population was 1.4 billion.",
        "The population was 1.4 billion.",
    )

    assert result.status == TemporalVerificationStatus.NOT_APPLICABLE


def test_same_date_matches():
    verifier = TemporalVerifier()

    result = verifier.verify(
        "The event occurred on 15/08/2024.",
        "The event occurred on 15/08/2024.",
    )

    assert result.status == TemporalVerificationStatus.MATCH


def test_different_dates_are_different():
    verifier = TemporalVerifier()

    result = verifier.verify(
        "The event occurred on 15/08/2024.",
        "The event occurred on 16/08/2024.",
    )

    assert result.status == TemporalVerificationStatus.DIFFERENT


def test_year_matches_specific_date_in_same_year():
    verifier = TemporalVerifier()

    result = verifier.verify(
        "The company reported results in 2024.",
        "The company reported results on 15/08/2024.",
    )

    assert result.status == TemporalVerificationStatus.MATCH


def test_different_years_do_not_match_specific_dates():
    verifier = TemporalVerifier()

    result = verifier.verify(
        "The company reported results in 2024.",
        "The company reported results on 15/08/2025.",
    )

    assert result.status == TemporalVerificationStatus.DIFFERENT


def test_same_quarter_matches():
    verifier = TemporalVerifier()

    result = verifier.verify(
        "Revenue increased in Q2 2024.",
        "Revenue increased during Q2 2024.",
    )

    assert result.status == TemporalVerificationStatus.MATCH


def test_different_quarters_are_different():
    verifier = TemporalVerifier()

    result = verifier.verify(
        "Revenue increased in Q2 2024.",
        "Revenue increased during Q3 2024.",
    )

    assert result.status == TemporalVerificationStatus.DIFFERENT


def test_same_month_matches():
    verifier = TemporalVerifier()

    result = verifier.verify(
        "Sales increased in March 2024.",
        "Sales increased during March 2024.",
    )

    assert result.status == TemporalVerificationStatus.MATCH


def test_different_months_are_different():
    verifier = TemporalVerifier()

    result = verifier.verify(
        "Sales increased in March 2024.",
        "Sales increased during April 2024.",
    )

    assert result.status == TemporalVerificationStatus.DIFFERENT


def test_same_relative_period_matches():
    verifier = TemporalVerifier()

    result = verifier.verify(
        "Revenue increased this year.",
        "Revenue increased this year.",
    )

    assert result.status == TemporalVerificationStatus.MATCH


def test_different_relative_periods_are_different():
    verifier = TemporalVerifier()

    result = verifier.verify(
        "Revenue increased this year.",
        "Revenue increased last year.",
    )

    assert result.status == TemporalVerificationStatus.DIFFERENT


def test_extracts_year():
    verifier = TemporalVerifier()

    values = verifier.extract_times(
        "The company grew significantly in 2024."
    )

    assert len(values) == 1
    assert values[0].value == 2024
    assert values[0].temporal_type == "year"


def test_extracts_date():
    verifier = TemporalVerifier()

    values = verifier.extract_times(
        "The event happened on 15/08/2024."
    )

    assert len(values) == 1
    assert values[0].value == 20240815
    assert values[0].temporal_type == "date"


def test_extracts_quarter():
    verifier = TemporalVerifier()

    values = verifier.extract_times(
        "Revenue increased in Q2 2024."
    )

    assert len(values) == 1
    assert values[0].value == 20242
    assert values[0].temporal_type == "quarter"


def test_extracts_month():
    verifier = TemporalVerifier()

    values = verifier.extract_times(
        "Sales increased in March 2024."
    )

    assert len(values) == 1
    assert values[0].value == 202403
    assert values[0].temporal_type == "month"


def test_empty_text():
    verifier = TemporalVerifier()

    assert verifier.extract_times("") == []


def test_none_text():
    verifier = TemporalVerifier()

    assert verifier.extract_times(None) == []