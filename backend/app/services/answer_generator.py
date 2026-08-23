from google import genai

from app.config import settings
from app.schemas.evidence import Evidence


class AnswerGenerator:
    """Generates an answer using retrieved evidence."""

    def __init__(self):
        # Create the Gemini client.
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

    def generate(
        self,
        question: str,
        evidence: list[Evidence],
    ) -> str:

        # Handle missing evidence.
        if not evidence:
            return "I could not find enough evidence to answer this question."

        # Prepare evidence for the model.
        context = "\n\n".join(
            f"Source: {item.source_name}\n"
            f"Content: {item.content}"
            for item in evidence
        )

        # Build an evidence-grounded prompt.
        prompt = f"""
You are ClarifyAI, an evidence-grounded question answering system.

Answer the user's question using ONLY the provided evidence.

Do not invent facts.
Do not use outside knowledge.
If the evidence is insufficient, clearly say so.
If sources contain different values, mention the difference and explain
that they may refer to different years or estimates.

Question:
{question}

Evidence:
{context}

Give a concise and factual answer.
"""

        response = self.client.models.generate_content(
    model=settings.gemini_model,
    contents=prompt,
    config={
        "temperature": 0,
    },
)
        return response.text.strip()