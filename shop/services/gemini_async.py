"""
Asynchronous Gemini API client using httpx.

Replaces the sync google-genai client for all AI operations.
Key benefits:
- Non-blocking I/O using httpx.AsyncClient
- True concurrency: process multiple requests in parallel
- Better resource utilization (fewer threads needed)
- Integrated timeout handling and retry logic
- Full structured logging with metrics

Usage:
    client = await get_async_gemini_client()
    response = await client.generate_content(
        model="gemini-2.5-flash",
        prompt="Your prompt here",
        user_id=123,
        task_id="task-uuid",
    )
"""

import httpx
import json
import time
import logging
from typing import Optional, Dict, Any

from shop.services.config import get_ai_config
from shop.services.ai_logger import ai_logger, AICallMetrics

logger = logging.getLogger(__name__)


class AsyncGeminiClient:
    """Async client for calling Gemini API via httpx."""

    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str, timeout: int = 30):
        """
        Initialize async Gemini client.

        Args:
            api_key: Gemini API key
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        logger.info(f"[AsyncGemini] Client initialized with timeout={timeout}s")

    async def generate_content(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: int = 400,
        user_id: Optional[int] = None,
        task_id: Optional[str] = None,
        event_name: str = "gemini_request",
        system_instruction: Optional[str] = None,
        response_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Call Gemini API asynchronously.

        Args:
            model: Model name (e.g., "gemini-2.5-flash")
            prompt: Input prompt text
            temperature: Temperature for generation (0-1)
            top_p: Top-p for sampling (0-1)
            max_tokens: Max output tokens
            user_id: Optional user ID for logging
            task_id: Optional Celery task ID for correlation
            event_name: Event name for structured logging
            system_instruction: Optional system prompt sent via Gemini's dedicated
                systemInstruction field (higher priority than conversation content,
                and not vulnerable to being overridden by injected history/messages)
            response_schema: Optional JSON schema. When set, the response is
                forced into application/json matching this schema (Gemini's
                native structured-output mode) instead of free-text JSON that
                has to be regex-parsed.

        Returns:
            Dict with keys:
                - "text": Generated text
                - "tokens_in": Input token count
                - "tokens_out": Output token count
                - "latency_ms": Response time
                - "status": "success"

        Raises:
            httpx.TimeoutException: If request times out
            httpx.HTTPError: If HTTP call fails
            Exception: For other API errors
        """
        config = get_ai_config()
        prompt_length = len(prompt)

        # Start logging with context manager
        with ai_logger.track_call(
            event_name, user_id, task_id, model, prompt_length
        ) as metrics:
            start_time = time.time()

            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(self.timeout)
                ) as client:
                    url = f"{self.GEMINI_API_URL}/{model}:generateContent"

                    generation_config = {
                        "temperature": temperature,
                        "topP": top_p,
                        "maxOutputTokens": max_tokens,
                    }
                    if response_schema is not None:
                        generation_config["responseMimeType"] = "application/json"
                        generation_config["responseSchema"] = response_schema

                    # Build request payload
                    payload = {
                        "contents": [
                            {
                                "role": "user",
                                "parts": [{"text": prompt}],
                            }
                        ],
                        "generationConfig": generation_config,
                    }
                    if system_instruction:
                        payload["systemInstruction"] = {
                            "parts": [{"text": system_instruction}]
                        }

                    headers = {
                        "Content-Type": "application/json",
                        "x-goog-api-key": self.api_key,
                    }

                    # Make async request
                    logger.debug(
                        f"[AsyncGemini] Calling {model} with prompt_len={prompt_length}"
                    )
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()

                    data = response.json()

                    # Extract text and token counts from response
                    text = ""
                    tokens_in = 0
                    tokens_out = 0

                    if "candidates" in data and data["candidates"]:
                        candidate = data["candidates"][0]
                        if (
                            "content" in candidate
                            and "parts" in candidate["content"]
                        ):
                            parts = candidate["content"]["parts"]
                            if parts and "text" in parts[0]:
                                text = parts[0]["text"]

                    if "usageMetadata" in data:
                        tokens_in = data["usageMetadata"].get("promptTokenCount", 0)
                        tokens_out = data["usageMetadata"].get(
                            "candidatesTokenCount", 0
                        )

                    latency_ms = (time.time() - start_time) * 1000

                    # Log success with metrics
                    ai_logger.log_call_success(
                        metrics,
                        response_length=len(text),
                        tokens_input=tokens_in,
                        tokens_output=tokens_out,
                        latency_ms=latency_ms,
                    )

                    logger.info(
                        f"[AsyncGemini] {event_name} success: "
                        f"{tokens_in}→{tokens_out} tokens in {latency_ms:.0f}ms"
                    )

                    return {
                        "text": text,
                        "tokens_in": tokens_in,
                        "tokens_out": tokens_out,
                        "latency_ms": latency_ms,
                        "status": "success",
                    }

            except httpx.TimeoutException as e:
                latency_ms = (time.time() - start_time) * 1000
                ai_logger.log_call_error(
                    metrics, "TimeoutError", str(e), latency_ms
                )
                logger.error(
                    f"[AsyncGemini] Timeout on {event_name} after {latency_ms:.0f}ms"
                )
                raise

            except httpx.HTTPStatusError as e:
                latency_ms = (time.time() - start_time) * 1000
                error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                ai_logger.log_call_error(
                    metrics, "HTTPStatusError", error_msg, latency_ms
                )
                logger.error(f"[AsyncGemini] HTTP error on {event_name}: {error_msg}")
                raise

            except httpx.HTTPError as e:
                latency_ms = (time.time() - start_time) * 1000
                ai_logger.log_call_error(
                    metrics, "HTTPError", str(e), latency_ms
                )
                logger.error(f"[AsyncGemini] HTTP error on {event_name}: {e}")
                raise

            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                ai_logger.log_call_error(
                    metrics, type(e).__name__, str(e), latency_ms
                )
                logger.error(
                    f"[AsyncGemini] Unexpected error on {event_name}: {e}",
                    exc_info=True,
                )
                raise

    async def embed_content(
        self,
        text: str,
        task_type: str,
        model: str = "gemini-embedding-001",
        output_dimensionality: int = 768,
    ) -> list[float]:
        """
        Embed a single piece of text asynchronously.

        Args:
            text: Text to embed
            task_type: "RETRIEVAL_DOCUMENT" for indexed content, "RETRIEVAL_QUERY"
                for search queries. Gemini's asymmetric embedding mode - using the
                right task_type on each side materially improves retrieval accuracy.
            model: Embedding model name
            output_dimensionality: Vector size (768 balances accuracy vs storage)

        Returns:
            list[float]: The embedding vector
        """
        vectors = await self.batch_embed_contents(
            [text], task_type, model=model, output_dimensionality=output_dimensionality
        )
        return vectors[0]

    async def batch_embed_contents(
        self,
        texts: list[str],
        task_type: str,
        model: str = "gemini-embedding-001",
        output_dimensionality: int = 768,
    ) -> list[list[float]]:
        """
        Embed multiple texts in a single round trip (used by the bulk seeding
        command to avoid one HTTP call per product).

        Returns:
            list[list[float]]: One embedding vector per input text, same order.
        """
        async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout)) as client:
            url = f"{self.GEMINI_API_URL}/{model}:batchEmbedContents"
            payload = {
                "requests": [
                    {
                        "model": f"models/{model}",
                        "content": {"parts": [{"text": text}]},
                        "taskType": task_type,
                        "outputDimensionality": output_dimensionality,
                    }
                    for text in texts
                ]
            }
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            }

            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            return [
                embedding["values"]
                for embedding in data.get("embeddings", [])
            ]


# Singleton async client (lazy-initialized)
_async_gemini_client: Optional[AsyncGeminiClient] = None


async def get_async_gemini_client() -> AsyncGeminiClient:
    """
    Get or create async Gemini client (singleton).

    Returns:
        AsyncGeminiClient: Async Gemini client instance

    Raises:
        ValueError: If GEMINI_API_KEY not configured
    """
    global _async_gemini_client
    if _async_gemini_client is None:
        config = get_ai_config()
        _async_gemini_client = AsyncGeminiClient(
            config.gemini_api_key, config.gemini_timeout
        )
    return _async_gemini_client
