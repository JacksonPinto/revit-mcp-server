"""
Configuration management for the Revit MCP Server.
Loads settings from environment variables and .env file.
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

# Load .env from project root
load_dotenv(dotenv_path=Path(__file__).parent / ".env")


class RevitConfig(BaseModel):
    """Configuration for the pyRevit Routes connection."""

    host: str = Field(default="localhost", description="pyRevit Routes host")
    port: int = Field(default=48884, description="pyRevit Routes port")
    timeout: float = Field(default=30.0, description="HTTP request timeout in seconds")
    max_retries: int = Field(default=3, description="Max retry attempts for failed requests")
    retry_backoff: float = Field(default=0.5, description="Retry backoff multiplier in seconds")

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


class AuthConfig(BaseModel):
    """Authentication and security configuration."""

    mode: Literal["none", "api_key", "jwt"] = Field(
        default="api_key",
        description="Auth mode: 'none' (dev only), 'api_key', or 'jwt'",
    )
    api_key: str | None = Field(
        default=None,
        description="Static API key for api_key mode. Auto-generated if not set.",
    )
    jwt_secret: str | None = Field(
        default=None,
        description="Secret for JWT signing (HS256). Required in jwt mode.",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_expiry_minutes: int = Field(default=60, description="JWT token expiry in minutes")
    allowed_hosts: list[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="Allowed client hostnames/IPs",
    )

    @field_validator("api_key", mode="before")
    @classmethod
    def generate_api_key_if_missing(cls, v: str | None) -> str:
        if v is None or v.strip() == "":
            key = secrets.token_hex(32)
            print(f"[revit-mcp-server] Generated API key: {key}")
            print("[revit-mcp-server] Set REVIT_MCP_API_KEY in your .env to persist this key.")
            return key
        return v


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    format: Literal["json", "console"] = Field(default="console")
    log_requests: bool = Field(default=True, description="Log all Revit API requests")
    log_responses: bool = Field(default=False, description="Log full API response payloads")


class ServerConfig(BaseModel):
    """Top-level MCP server configuration."""

    server_name: str = Field(default="revit-mcp-server")
    server_version: str = Field(default="1.0.0")
    revit: RevitConfig = Field(default_factory=RevitConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    unit_system: Literal["metric", "imperial"] = Field(
        default="metric",
        description="Input unit system. Metric = mm/m², Imperial = ft/ft²",
    )

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Build config from environment variables."""
        revit = RevitConfig(
            host=os.getenv("REVIT_HOST", "localhost"),
            port=int(os.getenv("REVIT_PORT", "48884")),
            timeout=float(os.getenv("REVIT_TIMEOUT", "30.0")),
            max_retries=int(os.getenv("REVIT_MAX_RETRIES", "3")),
        )
        auth = AuthConfig(
            mode=os.getenv("REVIT_MCP_AUTH_MODE", "api_key"),  # type: ignore[arg-type]
            api_key=os.getenv("REVIT_MCP_API_KEY"),
            jwt_secret=os.getenv("REVIT_MCP_JWT_SECRET"),
            jwt_expiry_minutes=int(os.getenv("REVIT_MCP_JWT_EXPIRY_MINUTES", "60")),
        )
        logging_cfg = LoggingConfig(
            level=os.getenv("REVIT_MCP_LOG_LEVEL", "INFO"),  # type: ignore[arg-type]
            format=os.getenv("REVIT_MCP_LOG_FORMAT", "console"),  # type: ignore[arg-type]
            log_requests=os.getenv("REVIT_MCP_LOG_REQUESTS", "true").lower() == "true",
        )
        return cls(
            revit=revit,
            auth=auth,
            logging=logging_cfg,
            unit_system=os.getenv("REVIT_MCP_UNIT_SYSTEM", "metric"),  # type: ignore[arg-type]
        )


# Global singleton
_config: ServerConfig | None = None


def get_config() -> ServerConfig:
    global _config
    if _config is None:
        _config = ServerConfig.from_env()
    return _config
