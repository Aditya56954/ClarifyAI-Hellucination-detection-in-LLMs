import re
from dataclasses import dataclass
from enum import Enum


class NumericVerificationStatus(str, Enum):
    """Possible outcomes of numerical comparison."""

    MATCH = "match"
    DIFFERENT = "different"
    INCOMPATIBLE = "incompatible"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class NumericValue:
    """A normalized numerical value extracted from text."""

    value: float
    unit: str | None
    normalized_value: float
    start: int
    end: int
    text: str
    quantity_type: str


@dataclass
class NumericVerificationResult:
    """Result of comparing numerical information in two texts."""

    status: NumericVerificationStatus
    claim_values: list[NumericValue]
    evidence_values: list[NumericValue]


class NumericVerifier:
    """
    Compares numerical claims against numerical evidence.

    Magnitude units such as million and billion are normalized before
    comparison. Quantity types such as percentages and currencies remain
    separate so incompatible quantities are not compared directly.
    """

    NUMBER_PATTERN = re.compile(
        r"""
        (?<![\w.-])
        (?P<prefix>[$€£₹])?
        (?P<number>
            (?:\d{1,3}(?:,\d{3})+|\d+)
            (?:\.\d+)?
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    UNIT_PATTERN = re.compile(
    r"""
    ^\s*
    (?P<unit>
        %
        |percent
        |percentage
        |thousand
        |million
        |billion
        |trillion
        |k
        |m
        |bn
        |tn
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

    UNIT_MULTIPLIERS = {
        "thousand": 1_000.0,
        "k": 1_000.0,
        "million": 1_000_000.0,
        "m": 1_000_000.0,
        "billion": 1_000_000_000.0,
        "bn": 1_000_000_000.0,
        "trillion": 1_000_000_000_000.0,
        "tn": 1_000_000_000_000.0,
    }

    PERCENT_UNITS = {
        "%",
        "percent",
        "percentage",
    }

    CURRENCY_SYMBOLS = {
        "$",
        "€",
        "£",
        "₹",
    }

    DEFAULT_RELATIVE_TOLERANCE = 0.02

    def __init__(
        self,
        relative_tolerance: float = DEFAULT_RELATIVE_TOLERANCE,
    ):
        if relative_tolerance < 0:
            raise ValueError(
                "relative_tolerance must be non-negative."
            )

        self.relative_tolerance = relative_tolerance

    def verify(
        self,
        claim: str,
        evidence: str,
    ) -> NumericVerificationResult:
        """Compare numerical information in a claim and evidence."""

        claim_values = self.extract_values(claim)
        evidence_values = self.extract_values(evidence)

        if not claim_values or not evidence_values:
            return NumericVerificationResult(
                status=NumericVerificationStatus.NOT_APPLICABLE,
                claim_values=claim_values,
                evidence_values=evidence_values,
            )

        if self._contains_incompatible_quantities(
            claim_values,
            evidence_values,
        ):
            return NumericVerificationResult(
                status=NumericVerificationStatus.INCOMPATIBLE,
                claim_values=claim_values,
                evidence_values=evidence_values,
            )

        if self._values_match(
            claim_values,
            evidence_values,
        ):
            status = NumericVerificationStatus.MATCH
        else:
            status = NumericVerificationStatus.DIFFERENT

        return NumericVerificationResult(
            status=status,
            claim_values=claim_values,
            evidence_values=evidence_values,
        )

    def extract_values(
        self,
        text: str,
    ) -> list[NumericValue]:
        """
        Extract numerical values and their surrounding units.

        Unit extraction is performed separately from number extraction
        so a sentence containing multiple values cannot cause a later
        unit to be skipped.
        """

        if not text:
            return []

        values = []

        for match in self.NUMBER_PATTERN.finditer(text):
            raw_number = match.group("number")
            prefix = match.group("prefix")

            try:
                value = float(raw_number.replace(",", ""))
            except ValueError:
                continue

            # Look immediately after the number for a magnitude or
            # percentage unit.
            suffix_start = match.end()
            suffix_text = text[suffix_start:]

            unit_match = self.UNIT_PATTERN.match(
                suffix_text
            )

            suffix = None

            if unit_match:
                suffix = unit_match.group("unit")

            unit = self._normalize_unit(suffix)

            quantity_type = self._determine_quantity_type(
                prefix,
                suffix,
            )

            normalized_value = self._normalize_value(
                value,
                unit,
            )

            end = match.end()

            if unit_match:
                end += unit_match.end()

            extracted_text = text[
                match.start():end
            ].strip()

            values.append(
                NumericValue(
                    value=value,
                    unit=unit,
                    normalized_value=normalized_value,
                    start=match.start(),
                    end=end,
                    text=extracted_text,
                    quantity_type=quantity_type,
                )
            )

        return values

    def _normalize_unit(
        self,
        suffix: str | None,
    ) -> str | None:
        """Normalize magnitude and percentage units."""

        if not suffix:
            return None

        normalized_suffix = suffix.strip().lower()

        if normalized_suffix in self.PERCENT_UNITS:
            return "percent"

        if normalized_suffix in self.UNIT_MULTIPLIERS:
            return normalized_suffix

        return None

    def _determine_quantity_type(
        self,
        prefix: str | None,
        suffix: str | None,
    ) -> str:
        """Determine whether the value is currency, percentage, or plain."""

        normalized_suffix = (
            suffix.strip().lower()
            if suffix
            else ""
        )

        if normalized_suffix in self.PERCENT_UNITS:
            return "percentage"

        if prefix in self.CURRENCY_SYMBOLS:
            return f"currency:{prefix}"

        return "number"

    def _normalize_value(
        self,
        value: float,
        unit: str | None,
    ) -> float:
        """Convert magnitude units into a base numeric value."""

        if unit == "percent":
            return value

        if unit in self.UNIT_MULTIPLIERS:
            return round(
                value * self.UNIT_MULTIPLIERS[unit]
            )

        return value

    def _values_match(
        self,
        claim_values: list[NumericValue],
        evidence_values: list[NumericValue],
    ) -> bool:
        """Check whether at least one comparable pair matches."""

        for claim_value in claim_values:
            for evidence_value in evidence_values:

                if not self._same_quantity_type(
                    claim_value,
                    evidence_value,
                ):
                    continue

                if self._approximately_equal(
                    claim_value.normalized_value,
                    evidence_value.normalized_value,
                ):
                    return True

        return False

    def _same_quantity_type(
        self,
        claim_value: NumericValue,
        evidence_value: NumericValue,
    ) -> bool:
        """Determine whether two values represent the same type."""

        return (
            claim_value.quantity_type
            == evidence_value.quantity_type
        )

    def _approximately_equal(
        self,
        first: float,
        second: float,
    ) -> bool:
        """Compare two values using relative tolerance."""

        if first == second:
            return True

        scale = max(
            abs(first),
            abs(second),
            1.0,
        )

        difference = abs(first - second)

        return difference / scale <= self.relative_tolerance

    def _contains_incompatible_quantities(
        self,
        claim_values: list[NumericValue],
        evidence_values: list[NumericValue],
    ) -> bool:
        """Detect numerical types that cannot be safely compared."""

        claim_types = {
            value.quantity_type
            for value in claim_values
        }

        evidence_types = {
            value.quantity_type
            for value in evidence_values
        }

        # Percentage cannot be directly compared with a currency
        # or plain numerical quantity.
        if "percentage" in claim_types:
            if evidence_types != {"percentage"}:
                return True

        if "percentage" in evidence_types:
            if claim_types != {"percentage"}:
                return True

        claim_currencies = {
            quantity_type
            for quantity_type in claim_types
            if quantity_type.startswith("currency:")
        }

        evidence_currencies = {
            quantity_type
            for quantity_type in evidence_types
            if quantity_type.startswith("currency:")
        }

        # Different currencies cannot be compared without exchange-rate
        # conversion.
        if (
            claim_currencies
            and evidence_currencies
            and claim_currencies != evidence_currencies
        ):
            return True

        return False