# Implementation Plan: Remote Frappe CLI Connection

**Branch**: `001-frappe-remote-cli` | **Date**: 2026-05-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-frappe-remote-cli/spec.md`

## Summary

The objective is to implement a command-line interface (CLI) tool using Click in Python that allows developers to interact with a remote Frappe site. The tool will support storing credentials in `~/.frappe-cli.json`, executing remote method invocations via `frappe.call`, and performing standard DocType CRUD operations. Output will default to human-readable tables, with a raw JSON output toggle (`--json`).

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: `click`, `requests`, `tabulate`, `pytest`
**Storage**: Local configuration file at `~/.frappe-cli.json`
**Testing**: `pytest`
**Target Platform**: Linux, macOS, Windows
**Project Type**: CLI / Python Library
**Performance Goals**: Command invocation overhead < 2s (plus network roundtrip)
**Constraints**: Strictly formatted stdout, robust error handling to stderr, standard POSIX exit codes
**Scale/Scope**: Single entry-point executable (`frappe-cli`) with multiple command groups (`config`, `call`, `doc`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Library-First**: The core HTTP client interacting with the Frappe API must be built as a standalone Python class/module (`FrappeClient`) independent of Click commands, allowing it to be imported as a library.
- **Principle II: CLI Interface**: Click commands must strictly parse input, delegate to the `FrappeClient` library, print tables/JSON to stdout, print error diagnostics to stderr, and exit with correct codes.
- **Principle III: Test-First**: Write unit and integration tests (mocking remote API requests using `responses` or `pytest-mock`) to verify CLI commands and client library behavior before final code implementation.
- **Principle IV: Simplicity**: Use plain `requests` library and Click features. Keep file formats and directories minimal.

## Project Structure

### Documentation (this feature)

```text
specs/001-frappe-remote-cli/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    └── cli-commands.json # JSON Schema of CLI inputs/outputs
```

### Source Code (repository root)

```text
src/
├── frappe_cli/
│   ├── __init__.py
│   ├── cli.py           # Main Click CLI command group and entry point
│   ├── client.py        # Standalone Frappe Client Library
│   ├── config.py        # Local JSON Configuration management
│   └── formatter.py     # Output formatting utilities (table/JSON)
tests/
├── __init__.py
├── test_client.py       # Unit tests for FrappeClient library
├── test_cli.py          # Integration tests for Click CLI
└── test_config.py       # Unit tests for local config management
```

**Structure Decision**: Single Python project structure in `src/frappe_cli` and `tests/` directories.

## Complexity Tracking

*No constitution violations identified; complexity tracking is not applicable.*
