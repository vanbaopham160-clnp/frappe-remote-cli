# Tasks: Remote Frappe CLI Connection

**Input**: Design documents from `/specs/001-frappe-remote-cli/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: TDD approach is required by the project constitution. Tests are written before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Single project: `src/frappe_cli/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan
- [X] T002 Initialize pyproject.toml at repository root with click, requests, and tabulate dependencies
- [X] T003 [P] Configure linting and formatting tools in pyproject.toml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement connection configuration management logic in src/frappe_cli/config.py
- [X] T005 [P] Create local config unit tests in tests/test_config.py
- [X] T006 [P] Create core FrappeClient wrapper structure in src/frappe_cli/client.py
- [X] T007 [P] Create unit tests for FrappeClient initialization in tests/test_client.py
- [X] T008 Implement terminal formatting utility in src/frappe_cli/formatter.py
- [X] T009 Implement base Click CLI group command and error handling in src/frappe_cli/cli.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Configure Remote Site Connection (Priority: P1) 🎯 MVP

**Goal**: Enable user to set, show, and check connection credentials stored locally in `~/.frappe-cli.json`.

**Independent Test**: Run `frappe-cli config set`, `frappe-cli config show`, and `frappe-cli config check` to verify configuration workflow.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Write integration tests for configuration CLI commands in tests/test_cli.py

### Implementation for User Story 1

- [X] T011 [US1] Implement CLI config commands in src/frappe_cli/cli.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Execute Remote Method Call (Priority: P1)

**Goal**: Trigger remote python method execution with parameters via `frappe.call` and return values.

**Independent Test**: Run `frappe-cli call <dotted_path> -p key val --json` and verify payload formats.

### Tests for User Story 2

- [X] T012 [P] [US2] Write unit and integration tests for remote method calling in tests/test_client.py and tests/test_cli.py

### Implementation for User Story 2

- [X] T013 [US2] Implement API call execution method in src/frappe_cli/client.py
- [X] T014 [US2] Implement Click call command in src/frappe_cli/cli.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Execute Document CRUD Operations (Priority: P2)

**Goal**: Read, list, create, update, and delete DocTypes on the remote Frappe site.

**Independent Test**: Use list/get/create/update/delete commands on a DocType and assert changes reflected on the server.

### Tests for User Story 3

- [X] T015 [P] [US3] Write unit and integration tests for DocType CRUD commands in tests/test_client.py and tests/test_cli.py

### Implementation for User Story 3

- [X] T016 [US3] Implement CRUD resource methods in src/frappe_cli/client.py
- [X] T017 [US3] Implement Click doc subcommands in src/frappe_cli/cli.py

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T018 [P] Update documentation and usage instructions in README.md
- [X] T019 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed sequentially in priority order (P1 → P2)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2)
- **User Story 2 (P1)**: Can start after Foundational (Phase 2)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Integrates with client methods but holds independent testing flows

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- Once Foundational phase completes, all user stories can start in parallel
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 2

```bash
# Launch tests for User Story 2 together:
Task: "Write unit and integration tests for remote method calling in tests/test_client.py and tests/test_cli.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently (MVP!)
3. Add User Story 2 → Test independently
4. Add User Story 3 → Test independently

### Multi-profile & Verification Enhancements (Phase 7)

1. Add tests for interactive prompts, profiles, and verification bypass → Verify failures.
2. Implement config migration and multi-profile schema in config.py.
3. Update cli.py to support interactive prompts and global --profile / --no-verify options.
4. Implement config use/list commands in cli.py.
5. Verify all tests pass.

---

## Phase 7: Multi-profile, Prompting & Verification Options (Priority: P2)

**Goal**: Support multiple site configurations, interactive prompting for missing config options, and SSL verification control.

### Tests for Phase 7
- [X] T020 [P] Write unit tests in tests/test_config.py for config migration, profile validation, and profile saving.
- [X] T021 [P] Write integration tests in tests/test_cli.py for interactive prompting, profile selection, config use/list subcommands, and --no-verify flags.

### Implementation for Phase 7
- [X] T022 [P] Implement config normalization, profile extraction, validation, and saving in src/frappe_cli/config.py.
- [X] T023 [P] Add global flags (--profile, --no-verify) to the root command group in src/frappe_cli/cli.py.
- [X] T024 [P] Update config set to support interactive prompts, profile option, and verify/no-verify switches in src/frappe_cli/cli.py.
- [X] T025 [P] Implement config use and config list subcommands in src/frappe_cli/cli.py.
- [X] T026 [P] Ensure FrappeClient instantiates with the correct verify option in src/frappe_cli/cli.py and propagates it to requests.

