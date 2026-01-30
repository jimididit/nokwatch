"""AI-powered content detection (OpenAI)."""
from .smart_detector import analyze_content
from .ai_config import is_ai_available, OPENAI_API_KEY

__all__ = ['analyze_content', 'is_ai_available', 'OPENAI_API_KEY']
