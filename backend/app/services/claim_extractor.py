import re


class ClaimExtractor:
    ATTRIBUTION_PREFIX_PATTERN = re.compile(
        r"^(?:according to [^,]+,\s*|reportedly,\s*|sources? (?:say|claim)s? that\s*)",
        re.IGNORECASE,
    )

    NOISE_MARKER_PATTERN = re.compile(r"\[[^\]]*\]")

    MIN_SENTENCE_LENGTH = 20
    MIN_SHORT_CLAIM_WORD_COUNT = 3

    def extract(self, text: str) -> list[str]:
        if not text:
            return []

        # Remove markdown characters
        text = re.sub(r"[*_>]", "", text)

        # Remove markdown headings
        text = re.sub(r"^\s*#+\s*.*$", "", text, flags=re.MULTILINE)

        # Replace table separators
        text = text.replace("|", " ")

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Split text into sentences
        sentences = re.split(r"(?<=[.!?])\s+|\n+", text)

        claims = []

        for sentence in sentences:
            sentence = sentence.strip()

            if not sentence:
                continue

            # Remove common attribution prefixes
            sentence = self.ATTRIBUTION_PREFIX_PATTERN.sub("", sentence).strip()

            if not sentence:
                continue

            # Questions are not claims
            if "?" in sentence:
                continue

            # Skip scraper noise
            if self.NOISE_MARKER_PATTERN.search(sentence):
                continue

            if len(sentence) >= self.MIN_SENTENCE_LENGTH:
                claims.append(sentence)
                continue

            if self._looks_like_short_factual_claim(sentence):
                claims.append(sentence)

        return self._deduplicate_claims(claims)

    def _looks_like_short_factual_claim(self, sentence: str) -> bool:
        words = self._tokenize(sentence)

        if len(words) < self.MIN_SHORT_CLAIM_WORD_COUNT:
            return False

        # Keep short claims containing numbers
        return any(char.isdigit() for char in sentence)

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\b[\w'-]+\b", text)

    def _deduplicate_claims(self, claims: list[str]) -> list[str]:
        seen = set()
        result = []

        for claim in claims:
            normalized = self._normalize_claim(claim)

            if normalized in seen:
                continue

            seen.add(normalized)
            result.append(claim)

        return result

    def _normalize_claim(self, claim: str) -> str:
        claim = claim.lower().strip()
        claim = re.sub(r"\s+", " ", claim)

        return claim