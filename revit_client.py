"""
HTTP client for communicating with the pyRevit Routes API running inside Revit.

pyRevit Routes runs a lightweight REST server on http://localhost:48884 inside the
Revit process. This client wraps all HTTP communication, handles retries, converts
units, and normalises error responses into typed exceptions.
"""

from __future__ import annotations

import asyncio
import json
import math
from typing import Any

import httpx
import structlog
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import RevitConfig, get_config

logger = structlog.get_logger(__name__)

# ------------------------------------------------------------------
# Unit conversion helpers
# ------------------------------------------------------------------

MM_PER_FOOT = 304.8
M2_PER_FT2 = 0.092903
M3_PER_FT3 = 0.028317


def mm_to_feet(mm: float) -> float:
    """Convert millimetres to Revit internal feet."""
    return mm / MM_PER_FOOT


def feet_to_mm(feet: float) -> float:
    """Convert Revit internal feet to millimetres."""
    return feet * MM_PER_FOOT


def sqm_to_sqft(sqm: float) -> float:
    return sqm / M2_PER_FT2


def sqft_to_sqm(sqft: float) -> float:
    return sqft * M2_PER_FT2


def cbm_to_cbft(cbm: float) -> float:
    return cbm / M3_PER_FT3


def cbft_to_cbm(cbft: float) -> float:
    return cbft * M3_PER_FT3


# ------------------------------------------------------------------
# Exception hierarchy
# ------------------------------------------------------------------


class RevitConnectionError(Exception):
    """Cannot connect to the pyRevit Routes server."""


class RevitAPIError(Exception):
    """Revit API returned an error response."""

    def __init__(self, message: str, status_code: int = 500, details: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


class RevitNotReadyError(RevitConnectionError):
    """Revit is open but no document is active or the Routes API is not ready."""


# ------------------------------------------------------------------
# Client
# ------------------------------------------------------------------


class RevitClient:
    """Async HTTP client for the pyRevit Routes API."""

    def __init__(self, config: RevitConfig | None = None):
        self.config = config or get_config().revit
        self._client: httpx.AsyncClient | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "RevitClient":
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=httpx.Timeout(self.config.timeout),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError(
                "RevitClient must be used as an async context manager. "
                "Use `async with RevitClient() as client:`"
            )
        return self._client

    # ------------------------------------------------------------------
    # Core request helpers
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
    ) -> Any:
        """Send a request with retry logic and structured error handling."""
        client = self._ensure_client()

        log = logger.bind(method=method, path=path)

        try:
            async for attempt in AsyncRetrying(
                retry=retry_if_exception_type(
                    (httpx.ConnectError, httpx.TimeoutException)
                ),
                stop=stop_after_attempt(self.config.max_retries),
                wait=wait_exponential(
                    multiplier=self.config.retry_backoff, min=0.2, max=5
                ),
                reraise=False,
            ):
                with attempt:
                    log.debug("sending request", attempt=attempt.retry_state.attempt_number)
                    response = await client.request(
                        method,
                        path,
                        params=params,
                        json=json_body,
                    )
                    return self._parse_response(response, path)

        except RetryError as e:
            raise RevitConnectionError(
                f"Failed to connect to Revit after {self.config.max_retries} attempts. "
                f"Ensure Revit is open and the pyRevit extension is loaded. "
                f"Base URL: {self.config.base_url}"
            ) from e
        except httpx.ConnectError as e:
            raise RevitConnectionError(
                f"Cannot connect to Revit at {self.config.base_url}. "
                "Check that Revit is running and pyRevit is installed."
            ) from e

    def _parse_response(self, response: httpx.Response, path: str) -> Any:
        """Parse HTTP response and raise typed errors."""
        if response.status_code == 404:
            raise RevitAPIError(
                f"Endpoint not found: {path}. Ensure the pyRevit extension is loaded.",
                status_code=404,
            )
        if response.status_code == 503:
            raise RevitNotReadyError(
                "Revit Routes API is not ready. Ensure a project is open in Revit."
            )
        if response.status_code >= 400:
            try:
                body = response.json()
                message = body.get("error") or body.get("message") or response.text
                details = body.get("details")
            except Exception:
                message = response.text
                details = None
            raise RevitAPIError(message, status_code=response.status_code, details=details)

        if response.status_code == 204 or not response.content:
            return {}

        try:
            return response.json()
        except json.JSONDecodeError:
            return {"raw": response.text}

    # ------------------------------------------------------------------
    # Public CRUD methods
    # ------------------------------------------------------------------

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, body: Any = None) -> Any:
        return await self._request("POST", path, json_body=body)

    async def put(self, path: str, body: Any = None) -> Any:
        return await self._request("PUT", path, json_body=body)

    async def delete(self, path: str, body: Any = None) -> Any:
        return await self._request("DELETE", path, json_body=body)

    # ------------------------------------------------------------------
    # Connectivity check
    # ------------------------------------------------------------------

    async def ping(self) -> dict[str, Any]:
        """Test the connection to Revit. Returns server info dict."""
        return await self.get("/revit/ping")

    async def is_connected(self) -> bool:
        """Return True if Revit is reachable."""
        try:
            await self.ping()
            return True
        except (RevitConnectionError, RevitNotReadyError):
            return False


# ------------------------------------------------------------------
# Module-level singleton factory
# ------------------------------------------------------------------

_client_instance: RevitClient | None = None


def get_revit_client() -> RevitClient:
    """Return a shared RevitClient instance (context manager still required)."""
    global _client_instance
    if _client_instance is None:
        _client_instance = RevitClient()
    return _client_instance
