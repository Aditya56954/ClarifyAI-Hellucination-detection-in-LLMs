import re
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.schemas.evidence import Evidence


class EvidenceDuplicateType(str, Enum):
    """Types of duplicate evidence detected by the deduplicator."""

    EXACT_URL = "exact_url"
    NORMALIZED_URL = "normalized_url"
    CONTENT = "content"


@dataclass
class EvidenceDeduplicationResult:
    """Result of deduplicating retrieved evidence."""

    unique_evidence: list[Evidence]
    duplicate_evidence: list[Evidence]


class EvidenceDeduplicator:
    """Removes duplicate evidence without collapsing independent sources."""

    TRACKING_PARAMETERS = {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "gclid",
        "fbclid",
    }

    # Conservative threshold for overall textual similarity.
    NEAR_DUPLICATE_THRESHOLD = 0.90

    # Very short text can produce unreliable similarity results.
    MIN_CONTENT_TOKENS = 8

    def deduplicate(
        self,
        evidence: list[Evidence],
    ) -> EvidenceDeduplicationResult:
        """
        Remove duplicate evidence while preserving independent sources.

        Duplicate detection happens at three levels:

        1. Normalized URL
        2. Normalized content
        3. Near-identical content from different URLs
        """

        unique_evidence = []
        duplicate_evidence = []

        seen_urls = set()
        seen_content = set()
        unique_contents = []

        for item in evidence:
            normalized_url = self._normalize_url(
                item.source_url
            )

            normalized_content = self._normalize_content(
                item.content
            )

            # Exact or normalized URL duplicate.
            if normalized_url in seen_urls:
                duplicate_evidence.append(item)
                continue

            # Exact content duplicate from another URL.
            if normalized_content in seen_content:
                duplicate_evidence.append(item)
                continue

            # Near-duplicate content from a different URL.
            is_copy = any(
                self._is_near_duplicate(
                    normalized_content,
                    existing_content,
                )
                for existing_content in unique_contents
            )

            if is_copy:
                duplicate_evidence.append(item)
                continue

            seen_urls.add(normalized_url)
            seen_content.add(normalized_content)
            unique_contents.append(normalized_content)

            unique_evidence.append(item)

        return EvidenceDeduplicationResult(
            unique_evidence=unique_evidence,
            duplicate_evidence=duplicate_evidence,
        )

    def _normalize_url(
        self,
        url: str | None,
    ) -> str:
        """Normalize URLs so tracking-only differences are ignored."""

        if not url:
            return ""

        parsed = urlsplit(url)

        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()

        # Remove trailing slash from normal paths.
        path = parsed.path.rstrip("/")

        # Remove common tracking parameters.
        query_parameters = [
            (key, value)
            for key, value in parse_qsl(
                parsed.query,
                keep_blank_values=True,
            )
            if key.lower() not in self.TRACKING_PARAMETERS
        ]

        # Query parameter order should not affect URL identity.
        query_parameters.sort()

        query = urlencode(query_parameters)

        # Fragments do not identify a different source document.
        return urlunsplit(
            (
                scheme,
                netloc,
                path,
                query,
                "",
            )
        )

    def _normalize_content(
        self,
        content: str,
    ) -> str:
        """Normalize text for exact-content comparison."""

        if not content:
            return ""

        # Normalize whitespace.
        content = re.sub(
            r"\s+",
            " ",
            content,
        ).strip()

        # Ignore capitalization.
        content = content.lower()

        # Ignore punctuation for duplicate comparison.
        content = re.sub(
            r"[^\w\s]",
            "",
            content,
        )

        return content

    def _is_near_duplicate(
        self,
        first: str,
        second: str,
    ) -> bool:
        """
        Check whether two pieces of content are highly similar.

        Both overall similarity and content containment are considered.
        Containment helps detect copied articles that have extra
        boilerplate or sentences appended to the original text.
        """

        first_tokens = self._tokenize_content(first)
        second_tokens = self._tokenize_content(second)

        if (
            len(first_tokens) < self.MIN_CONTENT_TOKENS
            or len(second_tokens) < self.MIN_CONTENT_TOKENS
        ):
            return False

        first_counts = Counter(first_tokens)
        second_counts = Counter(second_tokens)

        shared_tokens = sum(
            min(
                first_counts[token],
                second_counts[token],
            )
            for token in first_counts.keys()
            & second_counts.keys()
        )

        first_size = sum(first_counts.values())
        second_size = sum(second_counts.values())

        if not first_size or not second_size:
            return False

        # Sørensen-Dice similarity measures overall textual similarity.
        similarity = (
            2 * shared_tokens
        ) / (
            first_size + second_size
        )

        # Measure how much of the shorter text is contained
        # in the longer text.
        shorter_size = min(
            first_size,
            second_size,
        )

        containment = shared_tokens / shorter_size

        # Strong overall similarity indicates copied content.
        if similarity >= self.NEAR_DUPLICATE_THRESHOLD:
            return True

        # High containment catches copied content with added
        # boilerplate or extra sentences.
        return containment >= 0.95

    def _tokenize_content(
        self,
        content: str,
    ) -> list[str]:
        """Convert normalized content into comparable tokens."""

        return re.findall(
            r"\b\w+\b",
            content.lower(),
        )