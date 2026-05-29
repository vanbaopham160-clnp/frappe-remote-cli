# Implementation Plan: Interactive Prompts and TUI Configuration Setup

**Branch**: `003-interactive-prompts` | **Date**: 2026-05-29 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-interactive-prompts/spec.md`

## Summary

Enhance `frappe-cli` to provide an interactive user experience when managing configuration profiles. When arguments are omitted from commands (`config set`, `config use`, or `config remove`), the CLI will launch an interactive step-by-step TUI wizard or selection menu using `InquirerPy`. Headless environments (scripts, pipelines, MCP servers) will be detected automatically via TTY checks to bypass interactive prompts and avoid process freezes.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `click`, `requests`, `InquirerPy`, `tabulate`, `mcp`  
**Storage**: JSON configuration file (`~/.frappe-cli.json`), cache file (`~/.config/frappe-cli/version.json`)  
**Testing**: `pytest`, `click.testing.CliRunner`, mock patching of stdin/TTY  
**Target Platform**: Cross-platform (Linux, macOS, Windows)  
**Project Type**: CLI Application  
**Performance Goals**: Instant prompt loading (<50ms startup), instant TTY detection failure (<10ms).  
**Constraints**: Zero interactive blocking in non-TTY environments. Graceful exit on Ctrl+C.  
**Scale/Scope**: Updating 3 Click commands (`config_set`, `config_use`, `config_remove`) in `cli.py`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle 1: CLI Interface**: Standard arguments and option flags are preserved for automation. Interactive mode is a fallback, preserving headless inputs.
- **Principle 2: Test-First**: Write pytest unit tests using TTY mocking to verify prompt triggers and fallback conditions before finalize code.
- **Principle 3: Text I/O & Formatting**: Error outputs are written to stderr, results to stdout, with clean prompt rendering.

## Project Structure

### Documentation (this feature)

```text
specs/003-interactive-prompts/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── checklists/
    └── requirements.md  # Quality checklist file
```

### Source Code (repository root)

```text
src/
└── frappe_cli/
    ├── cli.py             # Add prompts integration and arg checks
    └── version_check.py   # Check PyPI updates

tests/
└── unit/
    ├── test_version_check.py
    └── test_interactive_prompts.py  # New test suite
```

**Structure Decision**: Single project layout mapping edits onto existing CLI files.

## Complexity Tracking

*No constitution violations.*
