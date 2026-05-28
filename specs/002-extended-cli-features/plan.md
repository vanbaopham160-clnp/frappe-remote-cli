# Implementation Plan: Extended Features and MCP Server

**Branch**: `002-extended-cli-features` | **Date**: 2026-05-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-extended-cli-features/spec.md`

## Summary

Enhance the Python-based `frappe-cli` tool to support advanced metadata listings, count records, execute server reports, perform multi-pass dynamic schema merges (resolving custom fields and overrides), execute client-side bulk operations, configure regional output formats (for dates and float values), and expose all tool operations natively via a Model Context Protocol (MCP) server.

## Technical Context

**Language/Version**: Python 3.8+  
**Primary Dependencies**: `click`, `requests`, `tabulate`, `mcp`, `rich` (optional, for spinner visual feedback)  
**Storage**: JSON Config (`~/.frappe-cli.json`), MCP Daemon State JSON (`~/.config/frappe-cli/mcp.json`)  
**Testing**: `pytest`, `pytest-mock`, unit and integration tests with request mocking  
**Target Platform**: Cross-platform (Linux, macOS, Windows)  
**Project Type**: CLI Application  
**Performance Goals**: Remote queries and schema merging completed in under 2 seconds under ordinary network conditions.  
**Constraints**: Zero global side effects, low memory footprint (<50MB RAM), standard session-based client authorization.  
**Scale/Scope**: Adding 8 new CLI commands, 15 MCP tool definitions, and formatting/schema resolver hooks.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle 1: CLI Interface**: Exposes all logic cleanly via stdin/args → stdout, and errors → stderr. Fully satisfied.
- **Principle 2: Test-First**: Write pytest validation checks prior to finalize code. Fully satisfied.
- **Principle 3: Text I/O & Formatting**: Native integration with date/number settings ensures standard representation. Fully satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/002-extended-cli-features/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli-contract.md  # CLI input/output definitions
└── tasks.md             # Phase 2 output (to be generated next)
```

### Source Code (repository root)

```text
src/
└── frappe_cli/
    ├── __init__.py
    ├── cli.py             # Main CLI router and click command definitions
    ├── client.py          # REST Client (Requests session, API calls, dynamic schema resolver)
    ├── config.py          # Config file parser and profile manager supporting format settings
    ├── formatter.py       # Outputs formatting layer applying number and date preferences
    └── mcp_server.py      # MCP server definition (stdio execution and detached daemon management)

tests/
├── unit/
│   ├── test_formatter.py
│   ├── test_schema.py
│   └── test_mcp.py
└── integration/
```

**Structure Decision**: Single project layout (Option 1) mapping code modifications onto the package files under `src/frappe_cli` and testing files under `tests/`.

## Complexity Tracking

*No violations of Project Constitution detected.*
