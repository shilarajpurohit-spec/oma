"""
OMA Agent — OpenRouter Client (Module 03)
Async wrapper for OpenRouter / DeepSeek R1 API calls.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

# ── Exceptions ────────────────────────────────────────────────────


class LLMError(Exception):
    """Raised when an LLM API call fails."""


class LLMEmptyResponseError(LLMError):
    """Raised when the LLM returns an empty response."""


# ── Client ────────────────────────────────────────────────────────


class OpenRouterClient:
    """Async client for OpenRouter chat completions."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.api_key = api_key or settings.openrouter_api_key
        self.base_url = (base_url or settings.openrouter_base_url).rstrip("/")
        self.model = model or settings.llm_model
        self.timeout = timeout

    # ── headers ───────────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/oma-agent",
            "X-Title": "OMA Agent",
        }

    # ── core call ─────────────────────────────────────────────────

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """Send a chat completion request and return the assistant text.

        Args:
            messages: List of {"role": ..., "content": ...} dicts.
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum tokens in the response.

        Returns:
            The assistant's reply as a plain string.

        Raises:
            LLMError: On HTTP or API errors.
            LLMEmptyResponseError: When the response contains no text.
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()

        except httpx.TimeoutException as exc:
            logger.error("LLM request timed out: %s", exc)
            raise LLMError(f"LLM request timed out after {self.timeout}s") from exc
        except httpx.HTTPStatusError as exc:
            logger.error("LLM HTTP error %s: %s", exc.response.status_code, exc.response.text)
            raise LLMError(
                f"LLM returned HTTP {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:
            logger.error("LLM request failed: %s", exc)
            raise LLMError(f"LLM request failed: {exc}") from exc

        data = resp.json()

        # Extract text from the OpenAI-compatible response
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            logger.error("Unexpected LLM response structure: %s", data)
            raise LLMEmptyResponseError(
                "LLM response missing choices[0].message.content"
            ) from exc

        if not content or not content.strip():
            raise LLMEmptyResponseError("LLM returned empty content")

        return content.strip()


# ── Singleton ─────────────────────────────────────────────────────
llm = OpenRouterClient()
