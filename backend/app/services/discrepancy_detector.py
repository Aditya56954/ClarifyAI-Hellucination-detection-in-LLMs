"""
Detects factual discrepancies between retrieved evidence sources.

Design overview
----------------
The detector is domain-independent: it never hardcodes rules for a
specific topic (capitals, GDP, CEOs, population, etc.). Instead it
derives a lightweight "proposition" from the user's question - a
subject entity and the attribute/relation being asked about it - and
uses that proposition as the primary anchor for deciding whether two
claims are actually competing answers to the same question, or simply
unrelated/complementary/noisy information.

Pipeline:

    QUESTION
        -> question proposition (subject, attribute, qualifiers)
        -> claim extraction per evidence source (with noise filtering)
        -> claim relevance filtering, anchored on the proposition when
           parsing succeeded (requiring the claim actually assert an
           answer, not just mention the subject/attribute)
        -> same-proposition compatibility (subject, attribute, metric
           qualifiers, temporal context) - REQUIRING both claims to
           actually assert an answer before they are ever compared,
           independent of how each claim entered the relevant set
        -> numeric tolerance pre-check
        -> semantic contradiction check (BART-MNLI via SemanticEvaluator)
        -> deduplicated discrepancies

BART-MNLI remains the final contradiction judge. Every heuristic gate
in this file exists only to decide whether a pair of claims is a
*plausible competitor* for the same proposition - never to decide, by
itself, that two claims contradict each other.
"""

import re
from itertools import combinations
from typing import Optional

from app.schemas.evidence import Evidence
from app.services.claim_extractor import ClaimExtractor
from app.services.semantic_evaluator import (
    SemanticEvaluator,
    SupportLabel,
)


class DiscrepancyDetector:
    """
    Detects factual discrepancies between retrieved evidence sources.

    The detector is intentionally domain-independent. It does not contain
    separate rules for GDP, population, capital, prices, dates, etc.

    The user's question is used to identify relevant factual claims first.
    Those claims are then compared with the semantic evaluator to determine
    whether two sources contain contradictory information.
    """

    # Common words that carry little factual meaning.
    STOP_WORDS = {
        "a", "an", "and", "are", "as", "at", "be", "been", "being", "but",
        "by", "can", "could", "did", "do", "does", "for", "from", "had",
        "has", "have", "he", "her", "his", "how", "i", "if", "in", "is",
        "it", "its", "many", "may", "might", "of", "on", "or", "our",
        "she", "that", "the", "their", "them", "there", "these", "they",
        "this", "those", "to", "was", "we", "were", "what", "when",
        "where", "which", "who", "why", "will", "with", "would", "you",
        "your",
    }

    # Words that describe the question rather than the factual subject.
    # This also absorbs precision/attribution qualifiers that describe
    # HOW a figure was produced (estimated, approximately, historical,
    # annual, average, projected, ...) rather than WHAT is being
    # measured, so they can never trigger a false "different
    # proposition" verdict and never inflate lexical overlap.
    GENERIC_WORDS = {
        "current", "currently", "latest", "recent", "recently",
        "approximately", "about", "around", "roughly", "estimated",
        "estimate", "estimates", "according", "reported", "reports",
        "source", "sources", "data", "information", "figure", "figures",
        "value", "values", "number", "numbers", "amount", "total",
        "overall", "official",
        "historical", "annual", "yearly", "average", "median",
        "projected", "forecast", "forecasted",
    }

    # Words that mark a claim as describing a *different sub-metric* than
    # the plain attribute (e.g. "GDP" vs "GDP per capita" vs "GDP
    # growth" vs "GDP at constant prices" vs "population change/added").
    # Two claims that disagree on membership in this set are describing
    # different propositions and must not be compared as contradictions.
    # Kept deliberately small and structural, not domain vocabulary.
    #
    # "current"/"constant" catch nominal vs. inflation-adjusted reporting
    # bases (a real, generic methodological distinction for any monetary
    # time series, not just GDP). "current" is intentionally also present
    # in TEMPORAL_MODIFIER_WORDS ("current CEO"); MODIFIER_WORDS is a
    # union of both sets, so this dual membership is harmless.
    #
    # The delta vocabulary (add/increase/decrease/gain/lose/...) catches
    # the generic "rate of change" vs. "absolute value" distinction -
    # e.g. "India will add 12.66 million in 2026" (a delta) is a
    # different proposition than "India's population is 1.476 billion"
    # (a total), even though both mention the same subject/attribute.
    # This generalizes to any metric phrased as a change rather than a
    # stock value (revenue, users, temperature, etc).
    METRIC_MODIFIER_WORDS = {
        "per", "capita", "growth", "grow", "grew", "rate", "nominal",
        "real", "constant", "current", "ppp", "purchasing",
        "add", "adds", "added", "adding",
        "increase", "increases", "increased", "increasing",
        "decrease", "decreases", "decreased", "decreasing",
        "gain", "gains", "gained", "gaining",
        "lose", "loses", "lost", "losing",
        "change", "changes", "changed", "net",
    }

    # Words that mark a claim as referring to a role/title at a different
    # point in time than "now".
    TEMPORAL_MODIFIER_WORDS = {
        "current", "currently", "former", "previously", "new",
        "incoming", "outgoing", "next", "future", "past", "upcoming",
    }

    MODIFIER_WORDS = METRIC_MODIFIER_WORDS | TEMPORAL_MODIFIER_WORDS

    # Verb-tense markers used for lightweight temporal reasoning. Only
    # consulted when explicit years do not already resolve the
    # comparison (see `_temporally_compatible`).
    #
    # PAST_MARKERS additionally includes generic role-transition /
    # event verbs (resigned, named, appointed, succeeded, ...). News
    # headlines routinely describe a *past* handover in present-tense
    # grammar ("X Resigns, Y Named CEO"), so without this a transition
    # announcement reads as a claim about "right now" and gets compared
    # against unrelated present-tense claims as if they were
    # simultaneous. This is a bias, not a certainty, and is documented
    # as a limitation below.
    PAST_MARKERS = {
        "was", "were", "had", "former", "previously", "historic",
        "historical",
        "resign", "resigns", "resigned", "resigning",
        "step", "steps", "stepped", "stepping",
        "named", "appoint", "appoints", "appointed",
        "succeed", "succeeds", "succeeded", "succeeding",
        "replace", "replaces", "replaced", "replacing",
        "elect", "elects", "elected",
    }
    FUTURE_MARKERS = {
        "will", "would", "shall", "upcoming", "incoming",
    }

    # Verbs/forms that indicate a claim is actually *asserting* something
    # about its subject, as opposed to a caption, nav fragment, or
    # imperative/descriptive snippet that merely mentions the right
    # keywords (e.g. "occupies", "sits alongside", "Discover the...").
    ASSERTION_VERBS = {
        "is", "are", "was", "were", "been", "being",
        "has", "have", "had",
        "serves", "serve", "served",
        "leads", "lead", "led",
        "became", "become", "becomes",
        "remains", "remain", "remained",
        "holds", "hold", "held",
        "named", "appointed", "appoints", "elected", "elects",
        "founded", "invented", "created", "discovered", "designed",
        "wrote", "directed", "built", "established", "released",
        "launched", "owns", "owned", "controls", "controlled",
        "manufactures", "produces", "stands", "represents", "represent",
        "isn't", "aren't", "wasn't", "weren't",
    }

    # Four-digit years are treated separately because they are useful
    # temporal constraints rather than ordinary keywords.
    YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")

    # Legacy / lightweight numeric extraction - kept for backwards
    # compatibility with any other callers of `_extract_numbers`.
    NUMBER_PATTERN = re.compile(
        r"""
        [-+]?
        (?:
            \d{1,3}(?:,\d{3})+
            |
            \d+(?:\.\d+)?
        )
        (?:
            \s*
            (?:%|percent|million|billion|trillion|thousand|crore|lakh)
        )?
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    # Structured numeric extraction used by the numeric-tolerance gate.
    # Captures an optional leading currency symbol, the numeric core, an
    # optional magnitude word, and an optional percent marker, as
    # separate named groups so units can be compared meaningfully.
    NUMERIC_VALUE_PATTERN = re.compile(
        r"""
        (?P<currency>[$€£₹])?
        \s*
        (?P<number>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)
        \s*
        (?P<multiplier>thousand|million|billion|trillion|crore|lakh)?
        \s*
        (?P<percent>%|percent)?
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    MULTIPLIER_MAP = {
        "thousand": 1e3,
        "million": 1e6,
        "billion": 1e9,
        "trillion": 1e12,
        "crore": 1e7,
        "lakh": 1e5,
    }

    # Matches calendar-date fragments ("August 08, 2026", "Date 04 Feb
    # 2025", "Saturday, July 25, 2026") so they can be stripped BEFORE
    # numeric extraction. Without this, the day-of-month digits inside a
    # date get picked up as if they were the actual factual value being
    # asserted, which is a generic problem with any web snippet that
    # timestamps a figure.
    _MONTH_NAMES = (
        r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
        r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t|tember)?|"
        r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
    )
    DATE_FRAGMENT_PATTERN = re.compile(
        rf"""
        (?:\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,?\s+)?
        \b(?:{_MONTH_NAMES})\.?\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s*(?:\d{{4}})?
        |
        \b\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{_MONTH_NAMES})\.?,?\s*(?:\d{{4}})?
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    # Strips leading attribution phrases so the underlying claim compares
    # cleanly (e.g. "According to X, Canberra is..." -> "Canberra is...").
    ATTRIBUTION_PREFIX_PATTERN = re.compile(
        r"^(?:according to [^,]+,\s*|reportedly,\s*|sources? (?:say|claim)s? that\s*)",
        re.IGNORECASE,
    )

    # Retrieval/scraping noise markers. A claim containing "[...]" is a
    # concatenation of unrelated fragments with omitted content spliced
    # together (nav menus, photo credits, table dumps) - it is not a
    # single coherent factual statement and must not be compared as one.
    NOISE_MARKER_PATTERN = re.compile(r"\[\s*\.\.\.\s*\]")

    # Used by `_has_answer_signal` to find clause boundaries (commas,
    # semicolons, dashes) so a structural "candidate near attribute near
    # verb" match cannot span across unrelated list items in the same
    # sentence (e.g. a bare list of "Capital Territory (Country), ...").
    CLAUSE_BREAK_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+|[,;\-\u2013\u2014]")

    # Heuristic factoid-question templates used to derive (subject,
    # attribute) pairs. These are deliberately generic (no named
    # entities) so they generalize across arbitrary domains. When none
    # of these match, the caller falls back to the original bag-of-words
    # relevance logic instead of guessing incorrectly.
    QUESTION_PATTERNS: list[re.Pattern] = [
        # "What/Who/Which is (the) ATTR of SUBJ"
        re.compile(
            r"^(?:what|who|which)\s+is\s+(?:the\s+)?(?P<attr>[a-z0-9\s\-']+?)"
            r"\s+of\s+(?P<subj>[a-z0-9\s\-']+?)[\?\.!]*$",
            re.IGNORECASE,
        ),
        # "What/Who/Which is (the) ATTR in SUBJ" (e.g. tallest mountain in X)
        re.compile(
            r"^(?:what|who|which)\s+is\s+(?:the\s+)?(?P<attr>[a-z0-9\s\-']+?)"
            r"\s+in\s+(?P<subj>[a-z0-9\s\-']+?)[\?\.!]*$",
            re.IGNORECASE,
        ),
        # "How many ATTR live in / are in / exist in SUBJ"
        re.compile(
            r"^how\s+many\s+(?P<attr>[a-z0-9\s\-']+?)\s+"
            r"(?:live\s+in|are(?:\s+there)?\s+in|exist\s+in)\s+"
            r"(?P<subj>[a-z0-9\s\-']+?)[\?\.!]*$",
            re.IGNORECASE,
        ),
        # "Who currently leads/heads/runs SUBJ"
        re.compile(
            r"^who\s+(?P<attr>currently\s+leads|leads|heads|runs)\s+"
            r"(?P<subj>[a-z0-9\s\-']+?)[\?\.!]*$",
            re.IGNORECASE,
        ),
        # "Tell me (about) SUBJ's ATTR"
        re.compile(
            r"^tell\s+me\s+(?:about\s+)?(?P<subj>[a-z0-9\s\-']+?)'s\s+"
            r"(?P<attr>[a-z0-9\s\-']+?)[\?\.!]*$",
            re.IGNORECASE,
        ),
        # Possessive form: "SUBJ's ATTR"
        re.compile(
            r"^(?:what\s+is\s+)?(?P<subj>[a-z0-9\s\-']+?)'s\s+"
            r"(?P<attr>[a-z0-9\s\-']+?)[\?\.!]*$",
            re.IGNORECASE,
        ),
        # "When was/did SUBJ founded/established/..."
        re.compile(
            r"^when\s+(?:was|did)\s+(?P<subj>[a-z0-9\s\-']+?)\s+"
            r"(?P<attr>founded|established|created|built|invented|released|launched)\b",
            re.IGNORECASE,
        ),
        # "Who invented/created/founded/discovered SUBJ"
        re.compile(
            r"^who\s+(?P<attr>invented|created|founded|discovered|designed|wrote|directed)"
            r"\s+(?P<subj>[a-z0-9\s\-']+?)[\?\.!]*$",
            re.IGNORECASE,
        ),
        # "Which company/country/person/organization owns/controls SUBJ"
        re.compile(
            r"^which\s+(?:company|country|person|organi[sz]ation)\s+"
            r"(?P<attr>owns|controls|manufactures|produces)\s+"
            r"(?P<subj>[a-z0-9\s\-']+?)[\?\.!]*$",
            re.IGNORECASE,
        ),
        # "What year did SUBJ win/happen/occur"
        re.compile(
            r"^what\s+year\s+did\s+(?P<subj>[a-z0-9\s\-']+?)\s+"
            r"(?P<attr>win|happen|occur)\b",
            re.IGNORECASE,
        ),
    ]

    # Baseline minimum claim length in characters. Sentences shorter than
    # this are still accepted when they look like a concrete, short
    # factual statement (see `_looks_like_short_factual_claim`) - this
    # prevents genuinely important short claims (e.g. "India's GDP is
    # $0.") from being discarded purely for brevity.
    MIN_SENTENCE_LENGTH = 20
    MIN_SHORT_CLAIM_WORD_COUNT = 3

    # A claim needs some meaningful lexical relationship with the question
    # before it is passed to the more expensive semantic model. Used only
    # as a fallback when question-proposition parsing fails.
    MIN_KEYWORD_OVERLAP = 1

    # Two claims need some common factual vocabulary before they are
    # considered candidates for semantic contradiction checking. Used
    # only as a fallback when question-proposition parsing fails.
    MIN_CLAIM_OVERLAP = 2

    # Numeric-tolerance thresholds (relative difference) used to decide
    # whether two numbers plausibly describe the same fact.
    NUMERIC_CLOSE_TOLERANCE = 0.01
    NUMERIC_CONTRADICTION_THRESHOLD = 0.25  # >=25% apart: worth flagging

    # Fuzzy word-matching guardrail: a prefix match is only trusted when
    # the two tokens are not wildly different in length, to avoid, e.g.,
    # "capital" incorrectly matching "capitalize".
    FUZZY_MATCH_MAX_LENGTH_DELTA = 4

    # Token-distance window used by the structural answer-signal check
    # in `_has_answer_signal` (see that method for the exact shape being
    # matched).
    ANSWER_SIGNAL_WINDOW = 6

    def __init__(self):
        # Load the services once and reuse them.
        self.evaluator = SemanticEvaluator()
        self.claim_extractor = ClaimExtractor()

    def detect(
        self,
        question: str,
        evidence: list[Evidence],
    ) -> list[str]:
        """
        Detect contradictions between evidence sources.

        The process is:

        1. Parse the question into a (subject, attribute) proposition
           when possible.
        2. Break retrieved evidence into individual claims, discarding
           scraping noise (fragments, interrogatives, concatenated dumps).
        3. Filter claims that are unrelated to the question / proposition,
           or that mention the right keywords without asserting an answer.
        4. Compare relevant claims from different sources, gated by
           temporal compatibility, an explicit answer-assertion check on
           BOTH claims, metric-modifier compatibility, and numeric
           tolerance.
        5. Use BART-MNLI as the final contradiction check.
        6. Remove duplicate discrepancy reports.
        """

        if not question or not evidence:
            return []

        if len(evidence) < 2:
            return []

        question_words = self._meaningful_words(self._tokenize(question))

        if not question_words:
            return []

        question_years = self._extract_years(question)

        # Attempt to identify what the question is actually asking about.
        # subject_words is None when no template matched - callers treat
        # that as "fall back to legacy bag-of-words behavior".
        subject_words, attribute_core_words, _attribute_modifiers = (
            self._parse_question_proposition(question)
        )

        # ---------------------------------------------------------
        # Extract relevant claims from every evidence source.
        # ---------------------------------------------------------

        source_claims = []

        for item in evidence:

            if not item.content:
                continue

            claims = self._extract_claims(item.content)

            relevant_claims = []

            for claim in claims:

                if not self._is_relevant_claim(
                    question,
                    question_words,
                    question_years,
                    claim,
                    subject_words=subject_words,
                    attribute_core_words=attribute_core_words,
                ):
                    continue

                relevant_claims.append(claim)

            if relevant_claims:
                # source_quality is optional on Evidence in principle -
                # be defensive rather than assuming it is always set.
                source_quality = getattr(item, "source_quality", None)
                source_claims.append(
                    (item.source_name, source_quality, relevant_claims)
                )

        # We need at least two different sources to establish
        # a source-to-source discrepancy.
        if len(source_claims) < 2:
            return []

        # ---------------------------------------------------------
        # Compare claims from different sources.
        # ---------------------------------------------------------

        discrepancies = []
        seen_pairs = set()

        for (
            first_source,
            first_quality,
            first_claims,
        ), (
            second_source,
            second_quality,
            second_claims,
        ) in combinations(source_claims, 2):

            for first_claim in first_claims:

                for second_claim in second_claims:

                    # Do not compare claims that clearly aren't competing
                    # for the same proposition (wrong subject, wrong
                    # sub-metric, non-asserting text, or different point
                    # in time).
                    if not self._claims_are_comparable(
                        first_claim,
                        second_claim,
                        question_words,
                        subject_words=subject_words,
                        attribute_core_words=attribute_core_words,
                    ):
                        continue

                    pair_key = self._pair_key(
                        first_source,
                        second_source,
                        first_claim,
                        second_claim,
                    )

                    if pair_key in seen_pairs:
                        continue

                    # -------------------------------------------------
                    # Numeric pre-check.
                    #
                    # If both claims contain numeric values with a
                    # matching unit and their dominant values are close,
                    # treat them as differing estimates rather than
                    # spending a semantic-model call on them. This is a
                    # PRE-CHECK only: it can rule a pair OUT (values are
                    # close), but it never rules a pair IN as a
                    # discrepancy by itself - that decision still belongs
                    # to the semantic evaluator below.
                    # -------------------------------------------------

                    if self._numeric_compatibility(first_claim, second_claim) is True:
                        continue

                    # -------------------------------------------------
                    # Semantic evaluation is the final decision maker.
                    #
                    # Lexical/temporal/numeric/answer-signal checks only
                    # reduce irrelevant comparisons. They do NOT by
                    # themselves determine whether two claims contradict.
                    # -------------------------------------------------

                    result = self.evaluator.evaluate(
                        first_claim,
                        second_claim,
                    )

                    if result != SupportLabel.CONTRADICTION:
                        continue

                    seen_pairs.add(pair_key)

                    discrepancies.append(
                        self._format_discrepancy(
                            first_source,
                            second_source,
                            first_claim,
                            second_claim,
                            first_quality,
                            second_quality,
                        )
                    )

        return discrepancies

    # =========================================================
    # CLAIM EXTRACTION
    # =========================================================

    def _extract_claims(
        self,
        text: str,
    ) -> list[str]:
        # Keep this wrapper for existing callers.
        return self.claim_extractor.extract(text)

    def _looks_like_short_factual_claim(self, sentence: str) -> bool:
        """
        Heuristic acceptance test for sentences below the normal minimum
        length: keep them only if they have enough word structure to be
        a statement (not a bare label/fragment) AND contain an explicit
        numeric value, since short claims worth preserving are almost
        always short *because* they are a terse number-bearing fact.
        """

        word_tokens = self._tokenize(sentence)

        if len(word_tokens) < self.MIN_SHORT_CLAIM_WORD_COUNT:
            return False

        return any(char.isdigit() for char in sentence)

    # =========================================================
    # QUESTION PROPOSITION PARSING
    # =========================================================

    def _parse_question_proposition(
        self,
        question: str,
    ) -> tuple[Optional[set[str]], Optional[set[str]], set[str]]:
        """
        Attempt to identify the proposition the question is asking about:
        a subject entity (e.g. "Australia") and the attribute/relation
        being requested about it (e.g. "capital").

        This is a heuristic, template-based parser, not a real semantic
        parser. When no template matches, callers fall back to the
        original bag-of-words relevance logic - that's safer than
        guessing incorrectly on unfamiliar phrasing.

        Returns (subject_words, attribute_core_words, attribute_modifiers).
        subject_words is None when parsing failed.
        """

        normalized = question.strip()

        for pattern in self.QUESTION_PATTERNS:

            match = pattern.match(normalized)

            if not match:
                continue

            groups = match.groupdict()
            attr_phrase = groups.get("attr", "") or ""
            subj_phrase = groups.get("subj", "") or ""

            subject_words = self._meaningful_words(self._tokenize(subj_phrase))

            if not subject_words:
                # This template matched syntactically but didn't yield a
                # usable subject (e.g. subject phrase was all stopwords).
                # Try the next template instead of returning a bad parse.
                continue

            attr_tokens = self._tokenize(attr_phrase)

            attribute_modifiers = {
                token for token in attr_tokens if token in self.MODIFIER_WORDS
            }

            attribute_core_words = {
                token
                for token in attr_tokens
                if token not in self.STOP_WORDS
                and token not in self.MODIFIER_WORDS
                and len(token) > 2
            }

            return subject_words, attribute_core_words, attribute_modifiers

        return None, None, set()

    # =========================================================
    # QUESTION RELEVANCE
    # =========================================================

    def _is_relevant_claim(
        self,
        question: str,
        question_words: set[str],
        question_years: set[str],
        claim: str,
        subject_words: Optional[set[str]] = None,
        attribute_core_words: Optional[set[str]] = None,
    ) -> bool:
        """
        Determine whether a retrieved sentence is plausibly answering
        the user's question.

        This is a RECALL-ORIENTED filter: it decides what is worth
        keeping as a *candidate*. It intentionally allows some claims
        through (via the semantic-model fallback) that merely look
        topically related, even if they don't structurally assert an
        answer - a claim that's relevant to the question but oddly
        phrased still deserves a chance to be considered.

        The corresponding PRECISION check - requiring both claims in a
        pair to actually assert an answer before they can be compared -
        happens later, in `_claims_are_comparable`, via
        `_has_answer_signal`. That is the gate that actually prevents
        two topically-related-but-non-asserting claims (tourism copy,
        navigation text, geographic description) from being reported as
        conflicting with each other. Keeping the two checks separate
        means a single non-asserting claim can still be *present* in the
        candidate set without ever being *compared* as if it were an
        answer.
        """

        claim_words = self._meaningful_words(self._tokenize(claim))

        if not claim_words:
            return False

        # ---------------------------------------------------------
        # Temporal filtering.
        #
        # If the question explicitly asks about a particular year and
        # the claim explicitly refers to another year, it should not
        # compete with the requested answer.
        # ---------------------------------------------------------

        claim_years = self._extract_years(claim)

        if question_years and claim_years:
            if not question_years.intersection(claim_years):
                return False

        # ---------------------------------------------------------
        # Proposition-aware relevance (preferred path).
        # ---------------------------------------------------------

        if subject_words:

            if not self._contains_matching_word(claim_words, subject_words):
                return False

            attribute_matches = bool(
                attribute_core_words
                and self._contains_matching_word(claim_words, attribute_core_words)
            )

            if attribute_matches and self._has_answer_signal(
                claim, subject_words, attribute_core_words
            ):
                return True

            # The attribute keyword is missing, or the claim mentions
            # the right words without actually asserting a value (a
            # caption, a heading, a list dump, a travel-copy aside).
            # Let the semantic model make the final relevance call
            # rather than accepting or rejecting on keyword overlap
            # alone - `_claims_are_comparable` will still require an
            # actual answer signal before any such claim can be
            # compared against another.
            result = self.evaluator.evaluate(question, claim)
            return result in {SupportLabel.ENTAILMENT, SupportLabel.CONTRADICTION}

        # ---------------------------------------------------------
        # Fallback: original lexical relevance check.
        # ---------------------------------------------------------

        overlap = question_words.intersection(claim_words)

        if len(overlap) >= self.MIN_KEYWORD_OVERLAP:
            return True

        # If lexical overlap is weak, let the semantic model decide
        # whether the claim is related to the question.
        result = self.evaluator.evaluate(question, claim)

        return result in {
            SupportLabel.ENTAILMENT,
            SupportLabel.CONTRADICTION,
        }

    def _has_answer_signal(
        self,
        claim: str,
        subject_words: Optional[set[str]],
        attribute_core_words: Optional[set[str]],
    ) -> bool:
        """
        Decide whether a claim actually looks like it is asserting a
        concrete answer to the question, as opposed to merely containing
        the subject/attribute vocabulary somewhere in a longer sentence
        (a list dump, a travel aside, a byline, a geographic description,
        an unrelated proper noun that happens to appear in the same
        sentence).

        Returns False immediately if `attribute_core_words` is empty -
        without a known attribute word to anchor against, the structural
        check below cannot run safely, and callers must not assume
        "answer signal present" in that case.

        Two signals qualify a claim:

        1. It contains an explicit numeric value - a number is, by
           itself, always a candidate answer for a factual question.
        2. It contains a capitalized "answer candidate" token that sits
           STRUCTURALLY close to the attribute word, with an assertion
           verb positioned BETWEEN the candidate and the attribute (or
           touching either end) - i.e. matches the shape "CANDIDATE is
           the ATTR of SUBJ" or "the ATTR of SUBJ is CANDIDATE" - and
           with no clause boundary (comma/dash/semicolon) separating
           them, so the match cannot span across an unrelated list item
           or a different clause in the same sentence.

           This is what distinguishes "Canberra is the capital of
           Australia" (candidate directly bound to "capital" via "is")
           from "Capital districts and territories ... Australian
           Capital Territory (Australia) ... Washington, D.C." (many
           capitalized tokens scattered across list items, none of them
           actually asserted as the answer), and from "The city occupies
           most of the northern quadrant of the Australian Capital
           Territory..." / "Getting to the Australian Capital Territory,
           where blissful nature sits..." (no assertion verb in
           ASSERTION_VERBS present at all - "occupies" and "sits" are
           descriptive/geographic verbs, not assertion verbs, so these
           claims fail signal #2 outright and have no digits, so they
           fail signal #1 too).

           A negated assertion verb ("isn't", "aren't") still counts -
           "Sydney isn't the capital of Australia" is structurally an
           answer-shaped claim about the same proposition, and whether
           it agrees or disagrees with a competing claim is exactly the
           kind of judgment the semantic contradiction model (not this
           heuristic gate) is meant to make.
        """

        if self._extract_numeric_values(claim):
            return True

        if not attribute_core_words:
            return False

        tokens = self._tokenize(claim)

        if not (set(tokens) & self.ASSERTION_VERBS):
            return False

        # Clause boundaries: token indices immediately after a comma,
        # semicolon, or dash. Used to reject matches that would span
        # across unrelated list items or clauses within one sentence.
        clause_break_positions = {
            i + 1
            for i, tok in enumerate(self.CLAUSE_BREAK_TOKEN_PATTERN.findall(claim.lower()))
            if tok in {",", ";", "-", "\u2013", "\u2014"}
        }

        attribute_positions = [
            i for i, tok in enumerate(tokens)
            if self._contains_matching_word({tok}, attribute_core_words)
        ]
        verb_positions = [i for i, tok in enumerate(tokens) if tok in self.ASSERTION_VERBS]

        if not attribute_positions or not verb_positions:
            return False

        excluded_words = set(subject_words or set()) | set(attribute_core_words)
        window = self.ANSWER_SIGNAL_WINDOW

        for raw_token in re.finditer(r"[A-Z][a-zA-Z]*", claim):

            lowered = raw_token.group(0).lower()

            if lowered in self.STOP_WORDS or lowered in self.GENERIC_WORDS:
                continue
            if lowered in self.MODIFIER_WORDS:
                continue
            if len(lowered) <= 2:
                continue
            if self._contains_matching_word({lowered}, excluded_words):
                continue

            candidate_positions = [i for i, tok in enumerate(tokens) if tok == lowered]
            if not candidate_positions:
                continue

            for candidate_position in candidate_positions:
                for attribute_position in attribute_positions:

                    if abs(candidate_position - attribute_position) > window:
                        continue

                    low, high = sorted((candidate_position, attribute_position))

                    # Reject if a clause boundary falls strictly between
                    # the candidate and the attribute - they belong to
                    # different list items / clauses.
                    if any(low < brk < high for brk in clause_break_positions):
                        continue

                    # Require an assertion verb positioned between (or
                    # touching) the candidate and the attribute - the
                    # actual "X is the Y of Z" / "Y of Z is X" shape,
                    # not just co-occurrence within a wide window.
                    if any(low <= vp <= high for vp in verb_positions):
                        return True

        return False

    # =========================================================
    # CLAIM COMPARISON
    # =========================================================

    def _claims_are_comparable(
        self,
        first_claim: str,
        second_claim: str,
        question_words: set[str],
        subject_words: Optional[set[str]] = None,
        attribute_core_words: Optional[set[str]] = None,
    ) -> bool:
        """
        Quickly determine whether two claims are worth sending to the
        semantic contradiction model.

        This is deliberately conservative. It is better to avoid
        comparing unrelated (or non-competing) sentences than to
        manufacture a contradiction between them.

        The question's proposition (subject + attribute), when known, is
        the PRIMARY anchor: two claims are comparable when they both
        refer to the same subject and the same requested attribute, both
        actually assert an answer (not merely mention the topic), and do
        not carry conflicting metric qualifiers. Lexical overlap between
        the two claims is only used as a fallback when the question
        could not be parsed into a proposition.
        """

        first_words = self._meaningful_words(self._tokenize(first_claim))
        second_words = self._meaningful_words(self._tokenize(second_claim))

        if not first_words or not second_words:
            return False

        # ---------------------------------------------------------
        # Temporal gate.
        #
        # Explicit years/dates are authoritative when present on both
        # sides; tense is only used as supporting evidence when explicit
        # temporal information is unavailable. See `_temporally_compatible`.
        # ---------------------------------------------------------

        if not self._temporally_compatible(
            self._temporal_context(first_claim),
            self._temporal_context(second_claim),
        ):
            return False

        # ---------------------------------------------------------
        # Proposition-anchored comparability (preferred path).
        # ---------------------------------------------------------

        if subject_words:

            if not self._contains_matching_word(first_words, subject_words):
                return False
            if not self._contains_matching_word(second_words, subject_words):
                return False

            if attribute_core_words:
                if not self._contains_matching_word(
                    first_words, attribute_core_words
                ):
                    return False
                if not self._contains_matching_word(
                    second_words, attribute_core_words
                ):
                    return False

            # Both claims must actually assert an answer to the
            # proposition - not merely mention subject/attribute
            # vocabulary in passing (tourism copy, navigation text,
            # geographic description). This check is UNCONDITIONAL
            # whenever subject_words matched - it does not sit inside
            # the `if attribute_core_words:` block above, so it can
            # never be silently skipped just because attribute parsing
            # came back empty. `_has_answer_signal` itself already
            # returns False when attribute_core_words is empty, so this
            # correctly degrades to "no answer signal possible" rather
            # than "check skipped" in that case.
            if not self._has_answer_signal(
                first_claim, subject_words, attribute_core_words
            ):
                return False
            if not self._has_answer_signal(
                second_claim, subject_words, attribute_core_words
            ):
                return False

            # Meaningful metric qualifiers (per capita, growth, nominal,
            # real, constant/current prices, delta/change vocabulary,
            # ...) mark a genuinely different proposition even when
            # subject and attribute both match (e.g. "GDP at constant
            # prices" vs "GDP at current prices", "population" vs
            # "population added", or "GDP" vs "GDP per capita").
            if self._modifiers_conflict(first_words, second_words):
                return False

            # Subject + attribute + both-sides-assert-an-answer +
            # compatible qualifiers is sufficient evidence that both
            # claims are competing answers to the same question.
            return True

        # ---------------------------------------------------------
        # Fallback: original lexical-overlap heuristic, used only when
        # the question's proposition could not be confidently parsed.
        # ---------------------------------------------------------

        if self._modifiers_conflict(first_words, second_words):
            return False

        common_words = first_words.intersection(second_words)

        if len(common_words) >= self.MIN_CLAIM_OVERLAP:
            return True

        # If both claims directly use important question vocabulary,
        # allow the semantic model to make the final decision.
        first_question_overlap = first_words.intersection(question_words)
        second_question_overlap = second_words.intersection(question_words)

        return bool(first_question_overlap and second_question_overlap)

    def _modifiers_conflict(
        self,
        first_words: set[str],
        second_words: set[str],
    ) -> bool:
        """
        Return True when the two claims are qualified by different
        metric modifiers (e.g. one says "per capita", the other doesn't;
        one says "at constant prices", the other doesn't; one describes
        a change/delta and the other an absolute value). This is a
        heuristic signal that the claims describe different sub-metrics,
        reporting bases, or value types of the same broad attribute and
        should not be compared directly.

        Incidental qualifiers (estimated, approximately, historical,
        annual, average, ...) are excluded from `METRIC_MODIFIER_WORDS`
        entirely (see `GENERIC_WORDS`), so they can never trigger a
        false conflict here.
        """

        first_modifiers = first_words & self.METRIC_MODIFIER_WORDS
        second_modifiers = second_words & self.METRIC_MODIFIER_WORDS

        return first_modifiers != second_modifiers

    # =========================================================
    # TEMPORAL REASONING
    # =========================================================

    def _temporal_context(self, text: str) -> tuple[set[str], str]:
        """
        Derive a lightweight temporal fingerprint for a claim: the
        explicit years it mentions, and a coarse tense classification
        ("past", "present", or "future") based on simple tense/event
        markers.

        This is heuristic and will miss subtler temporal cues, but it is
        enough to distinguish "X is CEO" from "Y will become CEO", and
        (via the transition-verb additions to PAST_MARKERS) to recognize
        that a headline like "X Resigns, Y Named CEO" narrates a past
        event even though it is grammatically present tense.
        """

        years = self._extract_years(text)
        tokens = set(self._tokenize(text))

        if tokens & self.FUTURE_MARKERS:
            tense = "future"
        elif tokens & self.PAST_MARKERS:
            tense = "past"
        else:
            tense = "present"

        return years, tense

    def _temporally_compatible(
        self,
        first_context: tuple[set[str], str],
        second_context: tuple[set[str], str],
    ) -> bool:
        """
        Decide whether two claims plausibly refer to the same point in
        time and can therefore be meaningfully compared.

        Explicit years are authoritative: when both claims name explicit
        years, agreement/disagreement between those years decides the
        outcome outright, regardless of tense (this correctly allows
        "Alice is CEO in 2026" vs "Bob was CEO until 2025" to be treated
        as non-competing, and "Alice is CEO in 2026" vs "Bob is CEO in
        2026" to be treated as competing).

        Tense is used only as a fallback signal when explicit years are
        not available on both sides to resolve the comparison.
        """

        first_years, first_tense = first_context
        second_years, second_tense = second_context

        if first_years and second_years:
            return bool(first_years.intersection(second_years))

        if first_tense != second_tense:
            return False

        return True

    # =========================================================
    # NUMERICAL REASONING
    # =========================================================

    def _extract_numeric_values(self, text: str) -> list[tuple[float, str]]:
        """
        Extract numeric values from a claim as (value, unit) pairs, with
        magnitude words (million/billion/...) already applied and a
        coarse unit classification ("plain", "percent", "currency") so
        that only like-for-like numbers get compared.

        Three categories of number are deliberately excluded, because
        none of them represents a magnitude/estimate of the attribute
        being asked about:

        - Years (handled separately by `_extract_years`).
        - Calendar-date fragments ("August 08, 2026", "04 Feb 2025") -
          stripped from a working copy of the text before scanning, so
          the day-of-month digit never gets mistaken for the claim's
          actual figure.
        - Ordinal numbers ("1st", "20th") - these denote rank/order, not
          a quantity, and must not be compared as if they were a
          magnitude for the requested attribute.
        """

        cleaned_text = self.DATE_FRAGMENT_PATTERN.sub(" ", text)

        values: list[tuple[float, str]] = []

        for match in self.NUMERIC_VALUE_PATTERN.finditer(cleaned_text):

            number_str = match.group("number")

            if not number_str:
                continue

            if self._looks_like_year(number_str):
                continue

            # Ordinal suffix check: skip "1st", "20th", "3rd", etc.
            tail = cleaned_text[match.end():match.end() + 2].lower()
            if tail in {"st", "nd", "rd", "th"}:
                continue

            try:
                value = float(number_str.replace(",", ""))
            except ValueError:
                continue

            multiplier = match.group("multiplier")
            if multiplier:
                value *= self.MULTIPLIER_MAP.get(multiplier.lower(), 1)

            if match.group("percent"):
                unit = "percent"
            elif match.group("currency"):
                unit = "currency"
            else:
                unit = "plain"

            values.append((value, unit))

        return values

    def _dominant_numeric_values_by_unit(self, text: str) -> dict[str, float]:
        """
        Reduce a claim's numeric values down to one *dominant* value per
        unit class: the largest-magnitude value seen for that unit.

        A single sentence can legitimately contain several numbers of
        the same unit (a headline figure alongside an incidental rank,
        a stray digit embedded in a citation marker, etc). Comparing
        every number against every number in the other claim risks
        pairing up two unrelated values purely because they happen to
        be numerically close - or, just as bad, letting a small
        incidental number stand in for the real figure. The value the
        sentence is actually asserting is, in practice, almost always
        the largest one for that unit, since date remnants, ranks, and
        citation digits are small by construction. This is a heuristic,
        not a guarantee.
        """

        dominant_values: dict[str, float] = {}

        for value, unit in self._extract_numeric_values(text):
            current = dominant_values.get(unit)
            if current is None or abs(value) > abs(current):
                dominant_values[unit] = value

        return dominant_values

    def _numeric_compatibility(
        self,
        first_claim: str,
        second_claim: str,
    ) -> Optional[bool]:
        """
        Compare the dominant explicit numeric values in two claims.

        Returns:
            True  - matching-unit dominant values are close enough to
                    plausibly represent the same underlying fact
                    (rounding, estimates, differing methodologies /
                    reference dates).
            False - matching-unit dominant values differ by enough that
                    they are unlikely to describe the same fact, and the
                    pair is worth sending to the semantic model.
            None  - no comparable numeric signal was found; the caller
                    should rely on the semantic model alone.
        """

        first_values = self._dominant_numeric_values_by_unit(first_claim)
        second_values = self._dominant_numeric_values_by_unit(second_claim)

        if not first_values or not second_values:
            return None

        found_close = False
        found_far = False

        for unit, first_value in first_values.items():

            if unit not in second_values:
                continue

            second_value = second_values[unit]
            larger = max(abs(first_value), abs(second_value))

            if larger == 0:
                # Both values are zero for this unit - genuinely equal,
                # not a discrepancy.
                found_close = True
                continue

            relative_diff = abs(first_value - second_value) / larger

            if relative_diff <= self.NUMERIC_CLOSE_TOLERANCE:
                found_close = True
            elif relative_diff >= self.NUMERIC_CONTRADICTION_THRESHOLD:
                found_far = True

        if found_close:
            return True
        if found_far:
            return False
        return None

    # =========================================================
    # NUMERICAL INFORMATION (legacy helper, kept for compatibility)
    # =========================================================

    def _extract_numbers(
        self,
        text: str,
    ) -> list[str]:
        """
        Extract explicit numerical values from a claim as raw strings.

        This method is kept generic because numbers can represent
        many different kinds of facts depending on the question.

        Superseded by `_extract_numeric_values` /
        `_dominant_numeric_values_by_unit` for the detector's own
        numeric-tolerance reasoning, but preserved as-is in case other
        parts of the codebase rely on this exact helper.
        """

        values = self.NUMBER_PATTERN.findall(text)

        return [
            re.sub(r"\s+", " ", value.strip().lower())
            for value in values
            if not self._looks_like_year(value.strip())
        ]

    # =========================================================
    # TOKENIZATION
    # =========================================================

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """
        Convert text into normalized word tokens.
        """

        return re.findall(
            r"[a-zA-Z0-9]+(?:[-'][a-zA-Z0-9]+)*",
            text.lower(),
        )

    def _meaningful_words(self, tokens: list[str]) -> set[str]:
        """
        Remove grammatical and generic words while keeping
        domain-specific vocabulary intact.

        No fixed list of factual domains is used.
        """

        words = set()

        for token in tokens:

            if token in self.STOP_WORDS:
                continue

            if token in self.GENERIC_WORDS:
                continue

            if self._looks_like_year(token):
                continue

            if token.isdigit():
                continue

            if len(token) <= 2:
                continue

            words.add(token)

        return words

    def _contains_matching_word(
        self,
        words: set[str],
        targets: set[str],
    ) -> bool:
        """
        Fuzzy membership check used as a lightweight stand-in for
        stemming/morphology (e.g. matching "Australia" against
        "Australian", or "found" against "founded").
        """

        for word in words:
            for target in targets:
                if self._words_fuzzy_match(word, target):
                    return True
        return False

    @classmethod
    def _words_fuzzy_match(cls, a: str, b: str) -> bool:
        """
        Two tokens are considered a match if they're identical, or if
        one is a prefix of the other, both are long enough that a short
        accidental prefix match is unlikely, and their length difference
        is small enough to avoid matching unrelated words that merely
        share a prefix (e.g. "capital" vs "capitalize").
        """

        if a == b:
            return True

        if len(a) < 4 or len(b) < 4:
            return False

        if abs(len(a) - len(b)) > cls.FUZZY_MATCH_MAX_LENGTH_DELTA:
            return False

        return a.startswith(b) or b.startswith(a)

    # =========================================================
    # TEMPORAL INFORMATION
    # =========================================================

    def _extract_years(self, text: str) -> set[str]:
        """
        Extract explicit four-digit years from text.
        """

        return set(self.YEAR_PATTERN.findall(text))

    @staticmethod
    def _looks_like_year(value: str) -> bool:
        """
        Check whether a token represents a four-digit year.
        """

        return bool(re.fullmatch(r"(?:19|20)\d{2}", str(value)))

    # =========================================================
    # DEDUPLICATION
    # =========================================================

    def _deduplicate_claims(self, claims: list[str]) -> list[str]:
        """
        Remove duplicate or nearly identical claims from the same source.
        """

        unique_claims = []
        seen = set()

        for claim in claims:

            normalized = self._normalize_claim(claim)

            if not normalized:
                continue

            if normalized in seen:
                continue

            seen.add(normalized)
            unique_claims.append(claim)

        return unique_claims

    @staticmethod
    def _normalize_claim(claim: str) -> str:
        """
        Normalize a claim for duplicate detection.
        """

        return " ".join(re.findall(r"[a-z0-9]+", claim.lower()))

    def _pair_key(
        self,
        first_source: str,
        second_source: str,
        first_claim: str,
        second_claim: str,
    ) -> tuple:
        """
        Create an order-independent key for a discrepancy.

        This prevents the same contradiction from being reported
        multiple times when retrieval contains duplicate chunks.
        """

        source_pair = tuple(sorted((first_source, second_source)))

        claim_pair = tuple(
            sorted(
                (
                    self._normalize_claim(first_claim),
                    self._normalize_claim(second_claim),
                )
            )
        )

        return (source_pair, claim_pair)

    # =========================================================
    # OUTPUT FORMATTING
    # =========================================================

    @staticmethod
    def _format_discrepancy(
        first_source: str,
        second_source: str,
        first_claim: str,
        second_claim: str,
        first_quality: Optional[str] = None,
        second_quality: Optional[str] = None,
    ) -> str:
        """
        Format a discrepancy for the existing ClarifyAI response layer.

        Source quality is appended as an optional, additive note (not a
        replacement for the core message) when both sources report a
        quality tier and those tiers differ - this surfaces the signal
        to the caller without the detector unilaterally discarding
        either source.
        """

        message = (
            f"{first_source} and "
            f"{second_source} report conflicting "
            f"information: "
            f"'{first_claim}' vs "
            f"'{second_claim}'"
        )

        if first_quality and second_quality and first_quality != second_quality:
            message += (
                f" (source quality — {first_source}: {first_quality}, "
                f"{second_source}: {second_quality})"
            )

        return message