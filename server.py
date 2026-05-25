"""
Revit MCP Server — Entry Point
==============================

A robust Model Context Protocol (MCP) server for Autodesk Revit.
Communicates with Revit via the pyRevit Routes API (HTTP on localhost:48884).

Usage:
    python server.py                    # stdio transport (Claude Desktop, etc.)
    python server.py --transport sse    # SSE transport

Or via the CLI entry point:
    revit-mcp-server
"""

from __future__ import annotations

import argparse
import asyncio
import sys

import structlog
from mcp.server import Server
from mcp.server.stdio import stdio_server

from config import get_config
from tools import register_all_tools

# ------------------------------------------------------------------
# Logging setup
# ------------------------------------------------------------------

def _configure_logging(level: str, fmt: str) -> None:
    import logging

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=getattr(logging, level, logging.INFO),
    )

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if fmt == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty()))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level, logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


# ------------------------------------------------------------------
# Server factory
# ------------------------------------------------------------------

def create_server() -> Server:
    """Build and return the configured MCP server."""
    config = get_config()
    _configure_logging(config.logging.level, config.logging.format)

    log = structlog.get_logger(__name__)
    log.info(
        "starting revit-mcp-server",
        version=config.server_version,
        revit_url=config.revit.base_url,
        auth_mode=config.auth.mode,
        unit_system=config.unit_system,
    )

    mcp = Server(
        name=config.server_name,
        version=config.server_version,
    )

    # Register all tool categories
    register_all_tools(mcp)

    log.info("tools registered", count=len(mcp.list_tools()))
    return mcp


# ------------------------------------------------------------------
# Transport runners
# ------------------------------------------------------------------

async def _run_stdio(mcp: Server) -> None:
    """Run the MCP server using stdio transport (default)."""
    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream,
            write_stream,
            mcp.create_initialization_options(),
        )


async def _run_sse(mcp: Server, host: str, port: int) -> None:
    """Run the MCP server using SSE transport."""
    try:
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Route, Mount
        import uvicorn
    except ImportError:
        print(
            "SSE transport requires extra packages:\n"
            "  pip install 'mcp[sse]' uvicorn starlette\n",
            file=sys.stderr,
        )
        sys.exit(1)

    sse = SseServerTransport("/messages")

    async def handle_sse(scope, receive, send):
        async with sse.connect_sse(scope, receive, send) as (r, w):
            await mcp.run(r, w, mcp.create_initialization_options())

    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages", app=sse.handle_post_message),
        ]
    )

    config_uv = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config_uv)
    print(f"[revit-mcp-server] SSE server running on http://{host}:{port}", file=sys.stderr)
    await server.serve()


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Revit MCP Server — AI tools for Autodesk Revit via pyRevit"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="MCP transport to use (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for SSE transport (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port for SSE transport (default: 3000)",
    )
    args = parser.parse_args()

    mcp = create_server()

    if args.transport == "sse":
        asyncio.run(_run_sse(mcp, args.host, args.port))
    else:
        asyncio.run(_run_stdio(mcp))


if __name__ == "__main__":
    main()
