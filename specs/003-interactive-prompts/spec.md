# Feature Specification: Interactive Prompts and TUI Configuration Setup

**Feature Branch**: `003-interactive-prompts`  
**Created**: 2026-05-29  
**Status**: Draft  
**Input**: User description: "Enhance CLI with InquiryPy for interactive configuration, profile switching, and profile removal prompts when arguments are omitted, while detecting non-interactive TTY environments to prevent hangs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Interactive Setup Wizard (Priority: P1)

Users want to configure their connection details and formatting options without typing long, complex command line options. When running setup, the system should guide them step-by-step.

**Why this priority**: Essential first-time UX. Relieves the user from having to remember option flag spellings and credentials formats.

**Independent Test**: Run `frappe-cli config set` with no flags. Walk through the interactive prompts for Site URL, API Key, API Secret, date format, and number format. Verify the configuration is successfully saved to `~/.frappe-cli.json`.

**Acceptance Scenarios**:

1. **Given** the user triggers `frappe-cli config set` without option flags, **When** they fill out the prompted fields and select "german" date and number format from the option lists, **Then** the CLI successfully writes the profile configuration to the JSON config file.
2. **Given** the user runs `frappe-cli config set`, **When** they press Enter to select default values or enter custom strings, **Then** all inputs are saved accurately.

---

### User Story 2 - Interactive Profile Selection & Removal (Priority: P1)

Users want to switch between profiles or remove profiles without typing the exact profile name. They require an interactive selection menu showing currently configured profiles.

**Why this priority**: Profile management is prone to spelling errors. Auto-suggesting configured profiles via interactive select lists prevents errors.

**Independent Test**: Configure two profiles: `dev` and `production`. Run `frappe-cli config use` (or `frappe-cli config remove`) without arguments. Verify a list menu is shown containing `dev` and `production` to choose from.

**Acceptance Scenarios**:

1. **Given** profiles `dev` and `production` exist, **When** running `frappe-cli config use` without arguments, **Then** the terminal displays a scrollable choice list containing both profiles. Selecting `production` updates the default active profile.
2. **Given** profiles exist, **When** running `frappe-cli config remove` without arguments, **Then** the terminal displays a choice list. Selecting a profile prompts for deletion confirmation and removes it.

---

### User Story 3 - Headless TTY Detection (Priority: P1)

AI assistants (like Claude, Cursor) and automated scripts (CI/CD) run commands in non-interactive shells. The CLI must detect when it is run in a headless environment and avoid displaying interactive selection lists (which would block/hang the process indefinitely).

**Why this priority**: Absolute requirement for safety. Ensures that automating the CLI inside scripts or MCP daemons never hangs.

**Independent Test**: Redirect stdin from `/dev/null` or run in a background script (non-interactive environment) and execute `frappe-cli config use`. Verify the command fails immediately with a clear error message instead of blocking.

**Acceptance Scenarios**:

1. **Given** the terminal execution environment has no interactive TTY (e.g. `sys.stdin.isatty()` is False), **When** running any interactive command like `frappe-cli config use`, **Then** the CLI fails immediately with exit code 1 and prints "Error: Stdin is not a TTY. Please provide the required arguments."
2. **Given** the CLI is running in MCP daemon mode, **When** the MCP server executes tool commands, **Then** the environment is treated as non-interactive and never prompts for input.

---

### Edge Cases

- **No Profiles Configured**: If a user runs `frappe-cli config use` or `config remove` when `profiles` dictionary is empty, it must immediately error with "Error: No profiles configured. Run 'frappe-cli config set' first." without showing empty select lists.
- **Ctrl+C / Interrupts during Prompts**: If the user cancels the prompts by pressing `Ctrl+C` or `Esc`, the CLI must exit cleanly with a message "Operation canceled" and exit code 1 (no raw python traceback should be displayed).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-101**: The system MUST use `InquirerPy` to handle interactive selections and text prompts.
- **FR-102**: If `config set` is invoked without options, the system MUST launch an interactive wizard:
  - Text prompt for `Site URL`
  - Text prompt for `API Key`
  - Password/hidden text prompt for `API Secret`
  - Select list for `Date Format` (options: `plain`, `us`, `french`, `german`)
  - Select list for `Number Format` (options: `plain`, `us`, `french`, `german`)
  - Text prompt for `Profile Name` (defaults to 'default')
- **FR-103**: If `config use` is invoked without a profile name argument, the system MUST present a select list of all configured profile names.
- **FR-104**: If `config remove` is invoked without a profile name argument, the system MUST present a select list of configured profile names to delete.
- **FR-105**: The system MUST detect if `sys.stdin.isatty()` is False or if `os.isatty(0)` is False. If detected as non-interactive, the CLI MUST bypass all `InquirerPy` menus and exit with error code 1, displaying: `Error: Input is not a TTY. Interactive prompts are unavailable.`
- **FR-106**: If the user cancels an interactive menu (via KeyboardInterrupt or prompt cancellation), the system MUST exit cleanly with code 1, printing: `Operation canceled.`

### Key Entities

- **Interactive Selection Menu**: Configured UI choices displayed in the terminal.
  - Attributes: `choices` (list of strings), `default` (string), `prompt_message` (string).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Interactive setup configurations are completed in under 30 seconds.
- **SC-002**: Commands executed in a headless pipe (e.g. `frappe-cli config use < /dev/null`) exit within 200ms with a clean non-TTY error.
- **SC-003**: In-process interruptions (like Ctrl+C during prompts) exit cleanly within 100ms without printing stack traces.

## Assumptions

- **A-001**: The environment supports ANSI colors and cursor control (standard for Unix, macOS, and modern Windows terminals).
- **A-002**: Pip packages for `InquirerPy` are available to be installed in the environment.
- **A-003**: Headless/non-interactive detection relies on standard Python `sys.stdin.isatty()` checks.
