# Tasks: Extended Features and MCP Server

**Input**: Design documents from `/specs/002-extended-cli-features/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Test tasks are included as requested by the TDD principles of the Spec Kit. Write tests first and ensure they fail before implementing the underlying features.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency updates

- [ ] T001 [P] Add `mcp` library to `dependencies` in `pyproject.toml`
- [ ] T002 [P] Configure ruff linting ignore rules for potential async/mcp libraries in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core settings parsing and output formatters required before story features can run

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Implement date and number format parsing in `src/frappe_cli/config.py`
- [ ] T004 Implement format validation functions in `src/frappe_cli/config.py`
- [ ] T005 [P] Create date and float value output formatting structures in `src/frappe_cli/formatter.py`
- [ ] T006 Setup Click CLI command routing structure placeholders for new commands in `src/frappe_cli/cli.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Localized Formatting & Metadata Retrieval (Priority: P1) 🎯 MVP

**Goal**: Support date/number formatting, document counts, profile removal, and metadata listings for reports/doctypes.

**Independent Test**: Configure formats, list records, count records, delete a profile, and retrieve listings of system doctypes and reports. Check output representations.

### Tests for User Story 1
- [ ] T007 [P] [US1] Create unit tests for date/number formatters in `tests/unit/test_formatter.py`
- [ ] T008 [P] [US1] Create unit tests for metadata lists and profile deletion command mocks in `tests/unit/test_metadata.py`

### Implementation for User Story 1
- [ ] T009 [US1] Update `config set` command flags (`--number-format`, `--date-format`) to write to configuration in `src/frappe_cli/cli.py`
- [ ] T010 [US1] Update `config show` command to output configuration as YAML or JSON formats in `src/frappe_cli/cli.py`
- [ ] T011 [US1] Implement `config remove <profile_name>` command logic in `src/frappe_cli/cli.py` and `src/frappe_cli/config.py`
- [ ] T012 [US1] Integrate formatting functions into stdout tables rendering logic in `src/frappe_cli/formatter.py`
- [ ] T013 [US1] Update `doc list` and `doc get` command options to apply formats before displaying in `src/frappe_cli/cli.py`
- [ ] T014 [US1] Implement REST count wrapper in `src/frappe_cli/client.py` and map to `doc count` in `src/frappe_cli/cli.py`
- [ ] T015 [US1] Implement metadata listing client helpers in `src/frappe_cli/client.py` and map to `meta doctypes` and `meta reports` commands in `src/frappe_cli/cli.py`

**Checkpoint**: User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 - Desk Report Execution (Priority: P1)

**Goal**: Execute query reports, zip columns with rows, and print report results as aligned tables.

**Independent Test**: Run a report by name with filters and verify columns and data lines display in the terminal correctly.

### Tests for User Story 2
- [ ] T016 [P] [US2] Create unit tests validating report array-zipping and table printing in `tests/unit/test_reports.py`

### Implementation for User Story 2
- [ ] T017 [US2] Implement REST API client method `run_report` in `src/frappe_cli/client.py`
- [ ] T018 [US2] Implement array and object row-parsing zip converters in `src/frappe_cli/formatter.py`
- [ ] T019 [US2] Implement the `report <report_name>` CLI command in `src/frappe_cli/cli.py`

**Checkpoint**: User Story 2 is fully functional and testable.

---

## Phase 5: User Story 3 - Dynamic Schema Resolution (Priority: P1)

**Goal**: Resolve doctypes, custom fields, and property setter option overrides in a unified schema definition.

**Independent Test**: Fetch the schema of a customized doctype and assert custom fields and Select options overrides are merged correctly.

### Tests for User Story 3
- [ ] T020 [P] [US3] Create unit tests verifying custom field injection indexes and property setter overrides in `tests/unit/test_schema.py`

### Implementation for User Story 3
- [ ] T021 [US3] Implement dynamic schema query and resolver logic `get_schema` in `src/frappe_cli/client.py`
- [ ] T022 [US3] Implement compact filtering logic for schema outputs in `src/frappe_cli/formatter.py`
- [ ] T023 [US3] Implement `schema <doctype>` CLI command in `src/frappe_cli/cli.py`

**Checkpoint**: User Story 3 is fully functional and testable.

---

## Phase 6: User Story 4 - Client-Side Bulk Actions (Priority: P2)

**Goal**: Perform bulk creates, updates, and deletes from local JSON structures with active progress feedback.

**Independent Test**: Create or delete multiple records in one CLI call and review status outputs.

### Tests for User Story 4
- [ ] T024 [P] [US4] Create unit tests checking bulk loop successes and exception catching in `tests/unit/test_bulk.py`

### Implementation for User Story 4
- [ ] T025 [US4] Implement sequential client-side loop CRUD helpers in `src/frappe_cli/client.py`
- [ ] T026 [US4] Implement bulk execution progress outputs and summary tables in `src/frappe_cli/formatter.py`
- [ ] T027 [US4] Implement `bulk create`, `bulk update`, and `bulk delete` commands in `src/frappe_cli/cli.py`

**Checkpoint**: User Story 4 is fully functional.

---

## Phase 7: User Story 5 - Model Context Protocol (MCP) Server Integration (Priority: P2)

**Goal**: Expose CLI methods as native AI agent tools over stdio or background-detached HTTP transport.

**Independent Test**: Start stdio MCP handshake, launch detached daemon, check daemon status, and stop daemon using stop commands.

### Tests for User Story 5
- [ ] T028 [P] [US5] Create unit tests asserting mcp tool calls and daemon control operations in `tests/unit/test_mcp.py`

### Implementation for User Story 5
- [ ] T029 [US5] Expose 15 CLI tool mappings in `src/frappe_cli/mcp_server.py` using Python MCP SDK
- [ ] T030 [US5] Implement standard input/output (stdio) handler in `src/frappe_cli/mcp_server.py`
- [ ] T031 [US5] Implement HTTP server transport in `src/frappe_cli/mcp_server.py`
- [ ] T032 [US5] Implement detached background daemon runner (`subprocess.Popen` detaching flags) in `src/frappe_cli/mcp_server.py`
- [ ] T033 [US5] Implement daemon state file storage (`mcp.json`) in `src/frappe_cli/mcp_server.py`
- [ ] T034 [US5] Create `mcp`, `mcp status`, and `mcp stop` commands in `src/frappe_cli/cli.py`

**Checkpoint**: All user stories are complete.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final formatting, documentation updates, and quickstart verification

- [ ] T035 [P] Clean code linting check and formatting run using Ruff across the repository
- [ ] T036 Update project `README.md` to document new options, bulk commands, and MCP usage instructions
- [ ] T037 Run validation checks from `specs/002-extended-cli-features/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Phase 1 completion. Blocks all user stories.
- **User Stories (Phases 3+)**: Depend on Phase 2. Can run in parallel or sequentially (US1 -> US2 -> US3 -> US4 -> US5).
- **Polish (Phase 8)**: Depends on completion of all user story tasks.

### Parallel Opportunities
- Setup tasks `T001` and `T002` can be run in parallel.
- Foundational tasks `T003`, `T004`, and `T005` can run in parallel.
- Test files `T007`, `T008`, `T016`, `T020`, `T024`, and `T028` can be written in parallel before coding.
- Once Phase 2 is complete, Phases 3, 4, 5, 6, and 7 can be worked on concurrently by different developers.

---

## Parallel Example: User Story 1

```bash
# Write both test files concurrently:
Task: "Create unit tests for date/number formatters in tests/unit/test_formatter.py"
Task: "Create unit tests for metadata lists and profile deletion command mocks in tests/unit/test_metadata.py"

# Build config updates in parallel:
Task: "Update config set command flags to write to configuration in src/frappe_cli/cli.py"
Task: "Implement config remove command logic in src/frappe_cli/cli.py and src/frappe_cli/config.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 1 (Setup) and Phase 2 (Foundational).
2. Complete Phase 3 (User Story 1).
3. **STOP and VALIDATE**: Run `tests/unit/test_formatter.py` and `tests/unit/test_metadata.py` to ensure core commands pass.
4. Ship/Demo the MVP (date/number formatting, metadata, profile config deletes, count check).

### Incremental Delivery
1. Foundation complete.
2. US1 complete → Test and release formatting + listing helpers.
3. US2 complete → Test and release Desk query report runs.
4. US3 complete → Test and release customized schema resolution.
5. US4 complete → Test and release sequential bulk CRUD loops.
6. US5 complete → Test and release stdio / detached background HTTP MCP daemon servers.
