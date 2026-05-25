"""Tests for the authentication module."""

from __future__ import annotations

import pytest

from auth import AuthError, AuthManager
from config import AuthConfig


def make_manager(mode: str = "api_key", api_key: str = "test-key-abc123") -> AuthManager:
    config = AuthConfig(mode=mode, api_key=api_key)  # type: ignore[arg-type]
    return AuthManager(config)


class TestApiKeyAuth:

    def test_valid_key_passes(self):
        mgr = make_manager("api_key", "my-secret-key")
        mgr.validate_request({"Authorization": "Bearer my-secret-key"})  # Should not raise

    def test_wrong_key_raises(self):
        mgr = make_manager("api_key", "my-secret-key")
        with pytest.raises(AuthError) as exc:
            mgr.validate_request({"Authorization": "Bearer wrong-key"})
        assert exc.value.status_code == 401

    def test_missing_header_raises(self):
        mgr = make_manager("api_key", "key")
        with pytest.raises(AuthError) as exc:
            mgr.validate_request({})
        assert exc.value.status_code == 401

    def test_non_bearer_scheme_raises(self):
        mgr = make_manager("api_key", "key")
        with pytest.raises(AuthError):
            mgr.validate_request({"Authorization": "Basic dXNlcjpwYXNz"})

    def test_lowercase_authorization_header(self):
        mgr = make_manager("api_key", "my-key")
        mgr.validate_request({"authorization": "Bearer my-key"})  # Should not raise


class TestNoneAuth:

    def test_no_header_passes_in_none_mode(self):
        mgr = make_manager("none")
        mgr.validate_request({})  # Should not raise

    def test_any_header_passes_in_none_mode(self):
        mgr = make_manager("none")
        mgr.validate_request({"Authorization": "Bearer garbage"})  # Should not raise


class TestJwtAuth:

    def setup_method(self):
        self.secret = "test-secret-for-jwt-unit-tests-minimum-32-chars"
        config = AuthConfig(mode="jwt", jwt_secret=self.secret, api_key="unused")  # type: ignore[arg-type]
        self.mgr = AuthManager(config)

    def test_issue_and_validate_token(self):
        token = self.mgr.issue_jwt("test-user")
        self.mgr.validate_request({"Authorization": f"Bearer {token}"})  # Should not raise

    def test_expired_token_raises(self):
        import time
        config = AuthConfig(mode="jwt", jwt_secret=self.secret, jwt_expiry_minutes=0, api_key="x")  # type: ignore[arg-type]
        mgr = AuthManager(config)
        # Issue a token that expires in 0 minutes (already expired)
        import jwt as pyjwt
        payload = {"sub": "u", "iat": int(time.time()) - 120, "exp": int(time.time()) - 60, "iss": "revit-mcp-server"}
        token = pyjwt.encode(payload, self.secret, algorithm="HS256")
        with pytest.raises(AuthError) as exc:
            self.mgr.validate_request({"Authorization": f"Bearer {token}"})
        assert exc.value.status_code == 401

    def test_invalid_signature_raises(self):
        token = self.mgr.issue_jwt("user")
        # Tamper with the token
        parts = token.split(".")
        parts[2] = "invalidsignature"
        bad_token = ".".join(parts)
        with pytest.raises(AuthError):
            self.mgr.validate_request({"Authorization": f"Bearer {bad_token}"})


class TestHostValidation:

    def test_allowed_host_passes(self):
        mgr = make_manager()
        mgr.validate_host("localhost")  # Should not raise

    def test_disallowed_host_raises(self):
        mgr = make_manager()
        with pytest.raises(AuthError) as exc:
            mgr.validate_host("evil.attacker.com")
        assert exc.value.status_code == 403
