from app.schemas.evidence import Evidence
from app.services.web_retriever import WebRetriever
from app.services.source_evaluator import SourceEvaluator


class Retriever:
    """Coordinates evidence retrieval."""

    def __init__(self):
        self.web_retriever = WebRetriever()
        self.source_evaluator = SourceEvaluator()

    def retrieve(self, question: str) -> list[Evidence]:
        # Retrieve evidence from the web.
        evidence = self.web_retriever.search(question)

        # Evaluate source quality.
        for item in evidence:
            item.source_quality = self.source_evaluator.evaluate(
                item.source_url
            )

        return evidence