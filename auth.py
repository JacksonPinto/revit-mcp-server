"""
Authentication and authorization middleware for the Revit MCP Server.

Supports three modes:
  - none     : No authentication (development only — never use in production)
  - api_key  : Static bearer token in Authorization header
  - jwt      : Short-lived JWT tokens with configurable expiry
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

import jwt as pyjwt

from config import AuthConfig, get_config


class AuthError(Exception):
    """Raised when authentication or authorization fails."""

    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.status_code = status_code


class AuthManager:
    """Handles authentication for all Revit MCP tool calls."""

    def __init__(self, config: AuthConfig | None = None):
        self.config = config or get_config().auth

    # ------------------------------------------------------------------
    # Token validation
    # ------------------------------------------------------------------

    def validate_request(self, headers: dict[str, str]) -> None:
        """Validate incoming request headers. Raises AuthError on failure."""
        if self.config.mode == "none":
            return

        auth_header = headers.get("Authorization") or headers.get("authorization")
        if not auth_header:
            raise AuthError("Missing Authorization header", 401)

        if not auth_header.startswith("Bearer "):
            raise AuthError("Authorization header must use Bearer scheme", 401)

        token = auth_header[len("Bearer "):]

        if self.config.mode == "api_key":
            self._validate_api_key(token)
        elif self.config.mode == "jwt":
            self._validate_jwt(token)

    def _validate_api_key(self, token: str) -> None:
        """Constant-time comparison of API keys to prevent timing attacks."""
        import hmac

        expected = self.config.api_key or ""
        if not hmac.compare_digest(token.encode(), expected.encode()):
            raise AuthError("Invalid API key", 401)

    def _validate_jwt(self, token: str) -> dict[str, Any]:
        """Decode and validate a JWT token."""
        if not self.config.jwt_secret:
            raise AuthError("JWT secret not configured on server", 500)
        try:
            payload = pyjwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm],
                options={"require": ["exp", "iat", "sub"]},
            )
            return payload
        except pyjwt.ExpiredSignatureError:
            raise AuthError("JWT token has expired", 401)
        except pyjwt.InvalidTokenError as e:
            raise AuthError(f"Invalid JWT token: {e}", 401)

    # ------------------------------------------------------------------
    # Token issuance (JWT mode)
    # ------------------------------------------------------------------

    def issue_jwt(self, subject: str, extra_claims: dict[str, Any] | None = None) -> str:
        """Issue a new JWT token (jwt mode only)."""
        if self.config.mode != "jwt":
            raise AuthError("JWT issuance only available in jwt auth mode", 400)
        if not self.config.jwt_secret:
            raise AuthError("JWT secret not configured", 500)

        now = int(time.time())
        payload: dict[str, Any] = {
            "sub": subject,
            "iat": now,
            "exp": now + (self.config.jwt_expiry_minutes * 60),
            "iss": "revit-mcp-server",
        }
        if extra_claims:
            payload.update(extra_claims)

        return pyjwt.encode(payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)

    def get_token_info(self, token: str) -> dict[str, Any]:
        """Return decoded JWT payload without verification (for inspection)."""
        return pyjwt.decode(token, options={"verify_signature": False})

    # ------------------------------------------------------------------
    # Host allowlist
    # ------------------------------------------------------------------

    def validate_host(self, host: str) -> None:
        """Ensure the connecting client is from an allowed host."""
        clean = host.split(":")[0]  # strip port if present
        if clean not in self.config.allowed_hosts:
            raise AuthError(f"Host '{clean}' is not in the allowed hosts list", 403)


# Global singleton
_auth_manager: AuthManager | None = None


def get_auth_manager() -> AuthManager:
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager
