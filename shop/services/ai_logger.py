"""
Structured logging for AI assistant operations.

Logs are output as JSON with structured fields, enabling:
- Real-time monitoring of AI API usage
- Token and cost tracking
- Performance metrics (latency, timeout analysis)
- Audit trail for compliance
- Error tracking and debugging

Logger name: "shop.ai_assistant"
Output format: JSON with keys: event, user_id, task_id, model, latency_ms,
               tokens_in, tokens_out, cost_usd, status, error_type, etc.
"""

import logging
import time
import json
from contextlib import contextmanager
from dataclasses import dataclass, asdict, field
from typing import Optional
from datetime import datetime

logger = logging.getLogger("shop.ai_assistant")


@dataclass
class AICallMetrics:
    """
    Track metrics for a single AI API call.

    Attributes:
        event: Operation type (e.g., "gemini_request", "intent_analysis")
        user_id: User making the request (None for anonymous)
        task_id: Celery task ID for correlation
        model: Model name used (e.g., "gemini-2.5-flash")
        prompt_length: Length of input prompt in characters
        response_length: Length of output response in characters (optional)
        latency_ms: Response time in milliseconds (optional)
        tokens_input: Input token count (optional)
        tokens_output: Output token count (optional)
        cost_usd: Estimated cost in USD (optional)
        status: Result status: "pending", "success", or "error"
        error_type: Exception type if failed (e.g., "TimeoutError")
        error_message: Error message if failed
        timestamp: ISO 8601 timestamp of the call
    """

    event: str
    user_id: Optional[int]
    task_id: Optional[str]
    model: str
    prompt_length: int
    response_length: Optional[int] = None
    latency_ms: Optional[float] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    cost_usd: Optional[float] = None
    status: str = "pending"
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_log_dict(self) -> dict:
        """
        Convert to structured log dictionary for JSON output.

        Returns:
            dict: Flattened dictionary with all fields
        """
        return {
            **asdict(self),
            "service": "ai_assistant",
            "log_level": "INFO" if self.status == "success" else "ERROR",
        }


class AIStructuredLogger:
    """Structured logger for AI operations."""

    @staticmethod
    def log_call_start(
        event: str,
        user_id: Optional[int],
        task_id: Optional[str],
        model: str,
        prompt_length: int,
    ) -> AICallMetrics:
        """
        Log the start of an AI API call.

        Args:
            event: Operation type
            user_id: Optional user ID
            task_id: Optional Celery task ID
            model: Model name
            prompt_length: Input length

        Returns:
            AICallMetrics: Metrics object for later updates
        """
        metrics = AICallMetrics(
            event=event,
            user_id=user_id,
            task_id=task_id,
            model=model,
            prompt_length=prompt_length,
            status="pending",
        )
        logger.info(json.dumps(metrics.to_log_dict()))
        return metrics

    @staticmethod
    def log_call_success(
        metrics: AICallMetrics,
        response_length: int,
        tokens_input: int,
        tokens_output: int,
        latency_ms: float,
    ) -> None:
        """
        Log successful AI API call with metrics.

        Args:
            metrics: Metrics object to update
            response_length: Output length
            tokens_input: Input token count
            tokens_output: Output token count
            latency_ms: Response time
        """
        metrics.response_length = response_length
        metrics.tokens_input = tokens_input
        metrics.tokens_output = tokens_output
        metrics.latency_ms = latency_ms
        metrics.status = "success"
        metrics.cost_usd = _estimate_cost(metrics.model, tokens_input, tokens_output)

        logger.info(json.dumps(metrics.to_log_dict()))

    @staticmethod
    def log_call_error(
        metrics: AICallMetrics,
        error_type: str,
        error_message: str,
        latency_ms: float,
    ) -> None:
        """
        Log failed AI API call.

        Args:
            metrics: Metrics object to update
            error_type: Exception class name
            error_message: Error message
            latency_ms: Elapsed time before failure
        """
        metrics.status = "error"
        metrics.error_type = error_type
        metrics.error_message = error_message
        metrics.latency_ms = latency_ms

        logger.error(json.dumps(metrics.to_log_dict()))

    @contextmanager
    def track_call(
        self,
        event: str,
        user_id: Optional[int],
        task_id: Optional[str],
        model: str,
        prompt_length: int,
    ):
        """
        Context manager for automatic timing and error logging.

        Automatically logs the start, captures timing, and logs success
        or error. Usage:

            with ai_logger.track_call("intent_analysis", user_id, task_id, model, len(prompt)):
                # Do work, may raise exception
                pass

        Yields:
            AICallMetrics: Metrics object (for manual logging if needed)
        """
        metrics = self.log_call_start(event, user_id, task_id, model, prompt_length)
        start_time = time.time()

        try:
            yield metrics
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.log_call_error(metrics, type(e).__name__, str(e), latency_ms)
            raise


def _estimate_cost(model: str, tokens_input: int, tokens_output: int) -> float:
    """
    Estimate cost of an API call based on model and token counts.

    Pricing reference (update as rates change):
    - Gemini 2.5 Flash: $0.075/1M input, $0.30/1M output tokens

    Args:
        model: Model name
        tokens_input: Input token count
        tokens_output: Output token count

    Returns:
        float: Estimated cost in USD, rounded to 6 decimal places
    """
    # Gemini 2.5 Flash pricing (verify with current rates)
    # Update these if pricing changes
    if "2.5-flash" in model.lower() or "flash-lite" in model.lower():
        input_cost_per_1m = 0.075  # $0.075 per 1M input tokens
        output_cost_per_1m = 0.30  # $0.30 per 1M output tokens
    else:
        # Default/fallback pricing
        input_cost_per_1m = 0.075
        output_cost_per_1m = 0.30

    cost = (tokens_input * input_cost_per_1m / 1_000_000) + (
        tokens_output * output_cost_per_1m / 1_000_000
    )
    return round(cost, 6)


# Singleton instance for use throughout the codebase
ai_logger = AIStructuredLogger()
