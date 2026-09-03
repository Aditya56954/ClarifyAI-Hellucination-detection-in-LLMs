import re
from dataclasses import dataclass
from enum import Enum


class TemporalVerificationStatus(str, Enum):
    """Possible outcomes of temporal comparison."""

    MATCH = "match"
    DIFFERENT = "different"
    INCOMPATIBLE = "incompatible"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class TemporalValue:
    """A temporal reference extracted from text."""

    value: int
    temporal_type: str
    start: int
    end: int
    text: str


@dataclass
class TemporalVerificationResult:
    """Result of comparing temporal information in two texts."""

    status: TemporalVerificationStatus
    claim_times: list[TemporalValue]
    evidence_times: list[TemporalValue]


class TemporalVerifier:
    """
    Compares temporal references in claims and evidence.

    Temporal differences are treated as differences in context, not
    automatic contradictions.
    """

    YEAR_PATTERN = re.compile(
        r"""
        (?<![\w])
        (?P<year>
            (?:18|19|20|21)\d{2}
        )
        (?![\w])
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    DATE_PATTERN = re.compile(
        r"""
        (?<![\w])
        (?P<date>
            (?:
                \d{1,2}
                [/-]
                \d{1,2}
                [/-]
                \d{2,4}
            )
            |
            (?:
                \d{4}
                [/-]
                \d{1,2}
                [/-]
                \d{1,2}
            )
        )
        (?![\w])
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    QUARTER_PATTERN = re.compile(
        r"""
        (?<![\w])
        (?P<quarter>
            Q[1-4]
            (?:\s+|[-/])
            (?:18|19|20|21)\d{2}
        )
        (?![\w])
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    MONTH_PATTERN = re.compile(
        r"""
        (?<![\w])
        (?P<month>
            (?:
                January|February|March|April|May|June|
                July|August|September|October|November|December
            )
            \s+
            (?:18|19|20|21)\d{2}
        )
        (?![\w])
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    RELATIVE_PERIOD_PATTERN = re.compile(
    r"\b(this year|last year|next year|this month|last month|next month|this quarter|last quarter|next quarter)\b",
    re.IGNORECASE,
)

    def verify(
        self,
        claim: str,
        evidence: str,
    ) -> TemporalVerificationResult:
        """Compare temporal information in a claim and evidence."""

        claim_times = self.extract_times(claim)
        evidence_times = self.extract_times(evidence)

        if not claim_times or not evidence_times:
            return TemporalVerificationResult(
                status=TemporalVerificationStatus.NOT_APPLICABLE,
                claim_times=claim_times,
                evidence_times=evidence_times,
            )

        if self._times_match(
            claim_times,
            evidence_times,
        ):
            status = TemporalVerificationStatus.MATCH
        else:
            status = TemporalVerificationStatus.DIFFERENT

        return TemporalVerificationResult(
            status=status,
            claim_times=claim_times,
            evidence_times=evidence_times,
        )

    def extract_times(
        self,
        text: str,
    ) -> list[TemporalValue]:
        """Extract recognizable temporal references from text."""

        if not text:
            return []

        matches: list[TemporalValue] = []

        # Extract explicit dates first.
        date_spans = []

        for match in self.DATE_PATTERN.finditer(text):
            value = self._parse_date_value(
                match.group("date")
            )

            if value is None:
                continue

            date_spans.append(
                (
                    match.start(),
                    match.end(),
                )
            )

            matches.append(
                TemporalValue(
                    value=value,
                    temporal_type="date",
                    start=match.start(),
                    end=match.end(),
                    text=match.group("date"),
                )
            )

        # Extract quarters.
        for match in self.QUARTER_PATTERN.finditer(text):
            if self._overlaps_existing_span(
                match.start(),
                match.end(),
                date_spans,
            ):
                continue

            quarter_value = self._parse_quarter_value(
                match.group("quarter")
            )

            if quarter_value is None:
                continue

            matches.append(
                TemporalValue(
                    value=quarter_value,
                    temporal_type="quarter",
                    start=match.start(),
                    end=match.end(),
                    text=match.group("quarter"),
                )
            )

        # Extract month + year references.
        for match in self.MONTH_PATTERN.finditer(text):
            if self._overlaps_existing_span(
                match.start(),
                match.end(),
                date_spans,
            ):
                continue

            month_value = self._parse_month_value(
                match.group("month")
            )

            if month_value is None:
                continue

            matches.append(
                TemporalValue(
                    value=month_value,
                    temporal_type="month",
                    start=match.start(),
                    end=match.end(),
                    text=match.group("month"),
                )
            )

        # Extract standalone years.
        occupied_spans = [
            (item.start, item.end)
            for item in matches
        ]

        for match in self.YEAR_PATTERN.finditer(text):
            if self._overlaps_existing_span(
                match.start(),
                match.end(),
                occupied_spans,
            ):
                continue

            year = int(match.group("year"))

            matches.append(
                TemporalValue(
                    value=year,
                    temporal_type="year",
                    start=match.start(),
                    end=match.end(),
                    text=match.group("year"),
                )
            )

        # Relative periods are kept as symbolic temporal references.
        for match in self.RELATIVE_PERIOD_PATTERN.finditer(text):
            matches.append(
                TemporalValue(
                    value=self._relative_period_value(
                        match.group(1)
                    ),
                    temporal_type="relative",
                    start=match.start(),
                    end=match.end(),
                    text=match.group(1),
                )
            )

                # Extract relative temporal periods such as "this year".
        for match in self.RELATIVE_PERIOD_PATTERN.finditer(text):
            matches.append(
                TemporalValue(
                    value=self._relative_period_value(
                        match.group(1)
                    ),
                    temporal_type="relative",
                    start=match.start(),
                    end=match.end(),
                    text=match.group(1),
                )
            )

                

        matches.sort(key=lambda item: item.start)

        return matches

    def _times_match(
        self,
        claim_times: list[TemporalValue],
        evidence_times: list[TemporalValue],
    ) -> bool:
        """
        Determine whether the texts contain a compatible temporal reference.

        Exact values are preferred. A year also matches a more specific
        date/month/quarter occurring within that same year.
        """

        for claim_time in claim_times:
            for evidence_time in evidence_times:

                if self._temporally_compatible(
                    claim_time,
                    evidence_time,
                ):
                    return True

        return False

    def _temporally_compatible(
        self,
        first: TemporalValue,
        second: TemporalValue,
    ) -> bool:
        """Check whether two temporal references describe the same period."""

        if first.temporal_type == "relative":
            return (
                second.temporal_type == "relative"
                and first.value == second.value
            )

        if second.temporal_type == "relative":
            return False

        if first.temporal_type == second.temporal_type:
            return first.value == second.value

        # A year is compatible with a more specific temporal reference
        # belonging to that year.
        if first.temporal_type == "year":
            return self._belongs_to_year(
                second,
                first.value,
            )

        if second.temporal_type == "year":
            return self._belongs_to_year(
                first,
                second.value,
            )

        return False

    def _belongs_to_year(
        self,
        temporal_value: TemporalValue,
        year: int,
    ) -> bool:
        """Check whether a temporal value belongs to a given year."""

        if temporal_value.temporal_type == "year":
            return temporal_value.value == year

        if temporal_value.temporal_type == "month":
            return temporal_value.value // 100 == year

        if temporal_value.temporal_type == "quarter":
            return temporal_value.value // 10 == year

        if temporal_value.temporal_type == "date":
            return temporal_value.value // 10_000 == year

        return False

    def _parse_date_value(
        self,
        text: str,
    ) -> int | None:
        """
        Convert a supported date into YYYYMMDD.

        The verifier intentionally supports only unambiguous numeric
        date formats here.
        """

        parts = re.split(
            r"[/-]",
            text,
        )

        if len(parts) != 3:
            return None

        try:
            first, second, third = (
                int(part)
                for part in parts
            )
        except ValueError:
            return None

        if first >= 1000:
            year = first
            month = second
            day = third
        else:
            day = first
            month = second
            year = third

            if year < 100:
                year += 2000

        if not 1 <= month <= 12:
            return None

        if not 1 <= day <= 31:
            return None

        return (
            year * 10_000
            + month * 100
            + day
        )

    def _parse_quarter_value(
        self,
        text: str,
    ) -> int | None:
        """Convert Qx YYYY into YYYYx."""

        match = re.search(
            r"Q([1-4])\s*[-/]?\s*((?:18|19|20|21)\d{2})",
            text,
            re.IGNORECASE,
        )

        if not match:
            return None

        quarter = int(match.group(1))
        year = int(match.group(2))

        return year * 10 + quarter

    def _parse_month_value(
        self,
        text: str,
    ) -> int | None:
        """Convert month + year into YYYYMM."""

        match = re.search(
            r"""
            (January|February|March|April|May|June|
             July|August|September|October|November|December)
            \s+
            ((?:18|19|20|21)\d{2})
            """,
            text,
            re.IGNORECASE | re.VERBOSE,
        )

        if not match:
            return None

        month_names = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
        }

        month = month_names[
            match.group(1).lower()
        ]

        year = int(match.group(2))

        return year * 100 + month

    def _relative_period_value(
        self,
        text: str,
    ) -> int:
        """Map relative periods to stable symbolic values."""

        normalized = text.lower().strip()

        values = {
            "this year": 1,
            "last year": 2,
            "next year": 3,
            "this month": 4,
            "last month": 5,
            "next month": 6,
            "this quarter": 7,
            "last quarter": 8,
            "next quarter": 9,
        }

        return values[normalized]

    def _overlaps_existing_span(
        self,
        start: int,
        end: int,
        spans: list[tuple[int, int]],
    ) -> bool:
        """Check whether a match overlaps another temporal reference."""

        for existing_start, existing_end in spans:
            if (
                start < existing_end
                and end > existing_start
            ):
                return True

        return False