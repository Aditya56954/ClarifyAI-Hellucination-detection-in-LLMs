class SourceEvaluator:
    """Evaluates the quality of a source."""

    HIGH_QUALITY_DOMAINS = {
        "worldbank.org",
        "imf.org",
        "gov.in",
        "nic.in",
    }

    MEDIUM_QUALITY_DOMAINS = {
        "reuters.com",
        "investopedia.com",
        "tradingeconomics.com",
    }

    def evaluate(self, source_url: str | None) -> float:
        # Return zero when no URL exists.
        if not source_url:
            return 0.0

        # Check trusted domains.
        for domain in self.HIGH_QUALITY_DOMAINS:
            if domain in source_url:
                return 1.0

        # Check established secondary sources.
        for domain in self.MEDIUM_QUALITY_DOMAINS:
            if domain in source_url:
                return 0.8

        # Default score for unknown sources.
        return 0.5