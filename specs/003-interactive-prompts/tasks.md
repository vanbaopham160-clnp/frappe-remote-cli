# Tasks: Interactive Prompts and TUI Configuration Setup

**Input**: Design documents from `/specs/003-interactive-prompts/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependency installation

- [X] T001 Add `InquirerPy` dependency to `pyproject.toml`
- [X] T002 Install dependencies locally using `.venv/bin/pip install -e .`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core TTY checks utilities

- [X] T003 [P] Implement `is_interactive()` TTY check utility function in `src/frappe_cli/config.py`
- [X] T004 Implement base TTY check unit tests in `tests/unit/test_interactive_prompts.py`

---

## Phase 3: User Story 1 - Interactive Setup Wizard (Priority: P1) 🎯 MVP

**Goal**: Support step-by-step interactive connection setup via InquirerPy

**Independent Test**: Run `frappe-cli config set` without options. Fill out prompts for site details and formatting. Verify details are saved to `~/.frappe-cli.json`.

### Tests for User Story 1
- [X] T005 [P] [US1] Create unit tests for interactive `config set` prompts in `tests/unit/test_interactive_prompts.py`

### Implementation for User Story 1
- [X] T006 [P] [US1] Create `prompt_profile_config()` wizard using InquirerPy in `src/frappe_cli/config.py`
- [X] T007 [US1] Integrate `prompt_profile_config` into `config_set` in `src/frappe_cli/cli.py`

---

## Phase 4: User Story 2 - Interactive Profile Selection & Removal (Priority: P1)

**Goal**: Support picking profiles using arrow-key list selections for `use` and `remove` subcommands

**Independent Test**: Configure multiple profiles. Run `frappe-cli config use` or `frappe-cli config remove` without arguments. Verify a select menu is shown.

### Tests for User Story 2
- [X] T008 [P] [US2] Create unit tests for interactive list selections in `tests/unit/test_interactive_prompts.py`

### Implementation for User Story 2
- [X] T009 [P] [US2] Create `prompt_profile_selection()` and deletion confirmation prompts in `src/frappe_cli/config.py`
- [X] T010 [US2] Integrate `prompt_profile_selection` into `config_use` in `src/frappe_cli/cli.py`
- [X] T011 [US2] Integrate selection and deletion prompts into `config_remove` in `src/frappe_cli/cli.py`

---

## Phase 5: User Story 3 - Headless TTY Detection (Priority: P1)

**Goal**: Ensure non-interactive shells exit immediately instead of waiting/blocking on input

**Independent Test**: Redirect stdin from `/dev/null` and verify commands exit instantly with code 1.

### Tests for User Story 3
- [X] T012 [P] [US3] Create unit tests mocking non-TTY standard input in `tests/unit/test_interactive_prompts.py`

### Implementation for User Story 3
- [X] T013 [US3] Add checks inside `config_set`, `config_use`, and `config_remove` in `src/frappe_cli/cli.py` to fail cleanly when TTY is inactive

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup, interrupt handling, and checklist validation

- [X] T014 [P] Catch `KeyboardInterrupt` inside interactive prompts in `src/frappe_cli/cli.py` to exit cleanly
- [X] T015 Verify all test suites (unit tests + integration tests) pass using `.venv/bin/pytest`

---

## Dependencies
`US1` -> `US2` -> `US3`
