"""AI-powered content analysis for change/category detection."""
import logging
from typing import Optional

from .ai_config import OPENAI_API_KEY, is_ai_available

logger = logging.getLogger(__name__)

# Max chars to send to API to stay within token limits
MAX_CONTENT_CHARS = 8000


def analyze_content(content: str, prompt: str) -> Optional[str]:
    """
    Send page content and user prompt to OpenAI for semantic analysis.
    Returns a short summary string, or None on error / no API key.
    """
    if not is_ai_available() or not (prompt or "").strip():
        return None
    content = (content or "").strip()
    if not content:
        return None
    if len(content) > MAX_CONTENT_CHARS:
        content = content[:MAX_CONTENT_CHARS] + "\n[... truncated]"
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You analyze web page content and answer the user's question in one short sentence or phrase. Be concise."
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\n---\nPage content:\n{content}"
                }
            ],
            max_tokens=150,
        )
        choice = response.choices and response.choices[0]
        if choice and choice.message and choice.message.content:
            return choice.message.content.strip()
    except Exception as e:
        logger.warning("AI analysis failed: %s", e)
    return None
