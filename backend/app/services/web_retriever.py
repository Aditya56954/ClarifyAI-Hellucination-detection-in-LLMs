from tavily import TavilyClient

from app.config import settings
from app.schemas.evidence import Evidence


class WebRetriever:
    """Retrieves evidence from web sources."""

    def __init__(self):
        self.client = TavilyClient(
            api_key=settings.tavily_api_key
        )

    def search(self, question: str) -> list[Evidence]:
        # Search the web for the question.
        response = self.client.search(
            query=question,
            max_results=5,
        )

        evidence = []

        # Convert search results into Evidence objects.
        for result in response.get("results", []):
            evidence.append(
                Evidence(
                    content=result.get("content", ""),
                    source_name=result.get("title", "Unknown Source"),
                    source_url=result.get("url"),
                    relevance_score=result.get("score"),
                )
            )

        return evidence