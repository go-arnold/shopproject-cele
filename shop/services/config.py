"""
Centralized configuration service for AI assistant.
All API keys, endpoints, and sensitive settings accessed here.

Security principle: Secrets are never hardcoded. All config comes from
environment variables or Django settings. This service is the single
access point.
"""

import os
from dataclasses import dataclass
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@dataclass
class AIConfig:
    """
    Immutable AI configuration object.
    Type-safe access to all AI settings.
    """

    gemini_api_key: str
    gemini_model: str
    gemini_timeout: int
    max_tokens: int
    temperature: float
    top_p: float
    max_history_messages: int
    max_message_length: int
    cache_timeout_seconds: int

    def __post_init__(self):
        """Validate that critical configuration is present."""
        if not self.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY not configured. "
                "Set the environment variable or GEMINI_API_KEY in Django settings."
            )

    def __repr__(self) -> str:
        """Redact sensitive info in string representation."""
        return (
            f"AIConfig("
            f"model={self.gemini_model}, "
            f"timeout={self.gemini_timeout}s, "
            f"max_tokens={self.max_tokens}, "
            f"temp={self.temperature}°, "
            f"api_key={'[REDACTED]'})"
        )


def get_ai_config() -> AIConfig:
    """
    Get AI configuration from environment/settings.

    Priority (highest to lowest):
    1. Environment variables (GEMINI_*)
    2. Django settings (GEMINI_API_KEY, etc.)
    3. Defaults

    Returns:
        AIConfig: Validated configuration object

    Raises:
        ValueError: If GEMINI_API_KEY is not set
    """
    # API key is mandatory
    api_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", "")

    if not api_key:
        logger.error(
            "GEMINI_API_KEY is not configured. "
            "AI assistant will not work. "
            "Set GEMINI_API_KEY environment variable or add to settings.py"
        )
        raise ValueError("GEMINI_API_KEY environment variable not set")

    return AIConfig(
        gemini_api_key=api_key,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        gemini_timeout=int(os.getenv("GEMINI_TIMEOUT", "30")),
        max_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "400")),
        temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.7")),
        top_p=float(os.getenv("GEMINI_TOP_P", "0.95")),
        max_history_messages=int(os.getenv("GEMINI_MAX_HISTORY", "6")),
        max_message_length=int(os.getenv("GEMINI_MAX_MESSAGE_LENGTH", "500")),
        cache_timeout_seconds=int(os.getenv("GEMINI_CACHE_TIMEOUT", "300")),
    )
