"""
Synchronous streaming Gemini client, used ONLY by the assistant's live chat
endpoint (shop/view_components/assistant/general.py:chat_stream).

Why sync, unlike the rest of this app's async-first Gemini client
(gemini_async.py): the project deploys under Gunicorn/WSGI (see
entrypoint.sh), not an ASGI server. Streaming a response body to the browser
via Django's StreamingHttpResponse under WSGI requires a plain synchronous
generator - the WSGI handler iterates it directly. Bridging an async
generator into that context buys no real concurrency (a single worker still
blocks for the duration of one streamed reply either way) and adds
complexity, so this stays a small, self-contained sync module rather than
forcing the async pattern where the deployment model doesn't support it.
"""

import json
import logging
from typing import Iterator, Optional

import httpx

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def stream_reply(
    api_key: str,
    model: str,
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.3,
    top_p: float = 0.95,
    max_tokens: int = 800,
    timeout: int = 30,
) -> Iterator[str]:
    """
    Stream plain-text reply chunks from Gemini as they're generated.

    Yields text deltas (not cumulative) as soon as each arrives. No JSON
    schema here on purpose - streaming a partial JSON blob can't be safely
    parsed/displayed incrementally, so this path returns plain reply text
    only. Intent/complaint classification happens as a separate, non-streamed
    call after the reply is fully generated (see assistant_service.classify_reply).
    """
    url = f"{GEMINI_API_URL}/{model}:streamGenerateContent"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "topP": top_p,
            "maxOutputTokens": max_tokens,
        },
    }
    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }

    with httpx.Client(timeout=httpx.Timeout(timeout)) as client:
        with client.stream(
            "POST", url, params={"alt": "sse"}, json=payload, headers=headers
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[len("data:"):].strip()
                if not data_str:
                    continue
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                candidates = chunk.get("candidates") or []
                if not candidates:
                    continue
                parts = candidates[0].get("content", {}).get("parts", [])
                for part in parts:
                    text = part.get("text")
                    if text:
                        yield text
