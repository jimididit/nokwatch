"""AI (OpenAI) configuration for smart content detection."""
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI API key; if not set, AI features are disabled
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()


def is_ai_available():
    """Return True if OpenAI API key is configured."""
    return bool(OPENAI_API_KEY)
