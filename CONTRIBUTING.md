# Contributing to revit-mcp-server

Thank you for wanting to contribute! This project follows standard open-source conventions.

## Development Setup

```bash
git clone https://github.com/jacksonpinto/revit-mcp-server.git
cd revit-mcp-server
pip install -e ".[dev]"
pre-commit install
```

## Adding a New Tool

1. Choose the appropriate module in `tools/` (or create a new one).
2. Add a `@mcp.tool()` decorated function with a comprehensive docstring.
   - The docstring is what the AI reads to understand when to use the tool.
   - Always document all parameters and return values.
3. Add the matching route handler in `pyrevit_extension/routes/`.
4. Register both in `tools/__init__.py` and `pyrevit_extension/startup.py`.
5. Add an example to `docs/examples/prompt_templates.md`.

## Code Style

- **Black** for formatting: `black .`
- **Ruff** for linting: `ruff check .`
- **Type hints** encouraged but not strictly enforced in pyRevit routes (IronPython compat)

## Pull Request Guidelines

- Small, focused PRs are preferred over large sweeping changes.
- Include a description of what Revit API feature is covered.
- All tools must have complete docstrings.
- If adding a new route, test it manually against a live Revit instance.

## Reporting Bugs

Open a GitHub issue with:
- Revit version
- pyRevit version
- The tool that failed
- The error message from the MCP server logs
- Steps to reproduce
