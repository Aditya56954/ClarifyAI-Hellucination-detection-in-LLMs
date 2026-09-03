from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlsplit

from app.schemas.evidence import Evidence
from app.services.evidence_deduplicator import EvidenceDeduplicator


class SourceIndependenceStatus(str, Enum):
    """Relationship between two evidence sources."""

    INDEPENDENT = "independent"
    NOT_INDEPENDENT = "not_independent"
    UNCERTAIN = "uncertain"


@dataclass
class SourceIndependenceResult:
    """Result of comparing two evidence items."""

    status: SourceIndependenceStatus
    reason: str


@dataclass
class EvidenceIndependenceGroup:
    """A group of evidence items carrying the same underlying information."""

    group_id: int
    evidence: list[Evidence]


class SourceIndependenceEvaluator:
    """
    Evaluates whether evidence items represent independent information.

    The evaluator does not attempt to determine which source is the
    original publisher. It only identifies evidence that is likely
    duplicated or independently reported.
    """

    def __init__(self):
        # Reuse the normalization and similarity rules already
        # established by EvidenceDeduplicator.
        self.deduplicator = EvidenceDeduplicator()

    def evaluate(
        self,
        first: Evidence,
        second: Evidence,
    ) -> SourceIndependenceResult:
        """
        Compare two evidence items and determine their independence.
        """

        first_content = self.deduplicator._normalize_content(
            first.content
        )

        second_content = self.deduplicator._normalize_content(
            second.content
        )

        # Empty normalized content cannot be compared reliably.
        if not first_content or not second_content:
            return SourceIndependenceResult(
                status=SourceIndependenceStatus.UNCERTAIN,
                reason="insufficient_content",
            )

        # Identical content is not independent.
        if first_content == second_content:
            return SourceIndependenceResult(
                status=SourceIndependenceStatus.NOT_INDEPENDENT,
                reason="identical_content",
            )

        # Near-identical content strongly suggests copied or syndicated
        # material even when the URLs are different.
        if self.deduplicator._is_near_duplicate(
            first_content,
            second_content,
        ):
            return SourceIndependenceResult(
                status=SourceIndependenceStatus.NOT_INDEPENDENT,
                reason="near_duplicate_content",
            )

        first_domain = self._extract_domain(
            first.source_url
        )

        second_domain = self._extract_domain(
            second.source_url
        )

        # Different domains with substantially different content are
        # treated as independent sources.
        if (
            first_domain
            and second_domain
            and first_domain != second_domain
        ):
            return SourceIndependenceResult(
                status=SourceIndependenceStatus.INDEPENDENT,
                reason="different_domains_and_content",
            )

        # Same-domain sources may still be independent articles.
        # Without stronger provenance information, keep this uncertain.
        return SourceIndependenceResult(
            status=SourceIndependenceStatus.UNCERTAIN,
            reason="same_domain_with_different_content",
        )

    def group_evidence(
        self,
        evidence: list[Evidence],
    ) -> list[EvidenceIndependenceGroup]:
        """
        Group evidence items by likely information independence.

        Evidence is assigned to an existing group when it is determined
        to be non-independent from any member of that group.

        Otherwise, a new independent group is created.
        """

        groups: list[EvidenceIndependenceGroup] = []

        for item in evidence:
            assigned_group = None

            for group in groups:
                for existing_item in group.evidence:
                    result = self.evaluate(
                        item,
                        existing_item,
                    )

                    if (
                        result.status
                        == SourceIndependenceStatus.NOT_INDEPENDENT
                    ):
                        assigned_group = group
                        break

                if assigned_group is not None:
                    break

            if assigned_group is None:
                assigned_group = EvidenceIndependenceGroup(
                    group_id=len(groups),
                    evidence=[],
                )

                groups.append(assigned_group)

            assigned_group.evidence.append(item)

        return groups

    def _extract_domain(
        self,
        url: str | None,
    ) -> str:
        """Extract a normalized domain from a source URL."""

        if not url:
            return ""

        parsed = urlsplit(url)

        return parsed.netloc.lower().removeprefix("www.")