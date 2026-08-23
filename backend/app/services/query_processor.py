import re


class QueryProcessor:
    """
    Responsible for preparing a user's question before it enters
    the main ClarifyAI processing pipeline.

    This component only handles query preprocessing.

    It does NOT:
    - call an LLM
    - search external sources
    - calculate confidence
    - generate the final answer
    """

    @staticmethod
    def normalize(question: str) -> str:
        """Clean and normalize the user's question."""

        # Remove whitespace from the beginning and end.
        question = question.strip()

        # Reduce multiple spaces to one.
        question = re.sub(r"\s+", " ", question)

        return question

    @staticmethod
    def validate(question: str) -> None:
        """Validate the normalized question."""

        # Reject empty questions.
        if not question:
            raise ValueError("Question cannot be empty.")