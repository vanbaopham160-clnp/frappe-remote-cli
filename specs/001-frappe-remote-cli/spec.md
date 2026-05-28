# Feature Specification: Remote Frappe CLI Connection

**Feature Branch**: `001-frappe-remote-cli`  
**Created**: 2026-05-28  
**Status**: Ready  
**Input**: User description: "i want use click to create cli to use call to a remote frappe site"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure Remote Site Connection (Priority: P1)

As a CLI user, I want to save connection credentials and URLs for a remote Frappe site to a local file, so that I don't have to input them for every command.

**Why this priority**: Establishing a secure configuration baseline is required before any communication can happen with the remote server.

**Independent Test**: Running the configuration setup flow writes the credentials to the local configuration file and validates connectivity.

**Acceptance Scenarios**:

1. **Given** the CLI is installed, **When** I run the configuration command and input a valid URL and API keys, **Then** the details are stored securely in `~/.frappe-cli.json` and a success confirmation is printed.
2. **Given** existing configurations, **When** I check connection status, **Then** the CLI performs a health-check call to the remote site and prints "Connected".

---

### User Story 2 - Execute Remote Method Call (Priority: P1)

As a CLI user, I want to trigger Python method calls on the remote Frappe site via the command line and view the returned execution output.

**Why this priority**: Calling remote Frappe methods is the primary requirement for integrating command-line operations with Frappe's backend logic.

**Independent Test**: Running a CLI execution command against a standard or custom whitelisted method on a live remote site returns the correct return values.

**Acceptance Scenarios**:

1. **Given** a configured connection, **When** I run the command to call a whitelisted method with parameters, **Then** the remote function is executed and its return data is outputted.
2. **Given** a method call that requires arguments, **When** I pass them as CLI options, **Then** they are properly serialized and sent to the remote site.

---

### User Story 3 - Execute Document CRUD Operations (Priority: P2)

As a CLI user, I want to perform basic operations (get, list, create) on DocTypes of the remote Frappe site.

**Why this priority**: Provides standard data manipulation tools directly from the command line, enhancing database administration.

**Independent Test**: Requesting a document schema or specific record by ID yields the matching structure.

**Acceptance Scenarios**:

1. **Given** a configured connection, **When** I request details of a document, **Then** the fields and values of that document are displayed.

---

### User Story 4 - Multi-profile Management (Priority: P2)

As a CLI user, I want to manage multiple site configuration profiles and switch between them easily, so that I can interact with dev, staging, and production sites using the same tool.

**Why this priority**: Crucial for developers working across multiple Frappe sites.

**Independent Test**: Configuring multiple profiles and switching between them succeeds, and running a call executes on the active profile's URL.

**Acceptance Scenarios**:
1. **Given** multiple profiles configured, **When** I run `config use <profile>`, **Then** that profile becomes the active default.
2. **Given** multiple profiles, **When** I run `frappe-cli --profile <profile> config check`, **Then** it tests connection specifically for that profile.

---

### User Story 5 - Interactive Config Setup (Priority: P2)

As a CLI user, I want to be prompted interactively for credentials when running `config set` without arguments, so that I do not have to write long commands containing sensitive secrets in my shell history.

**Independent Test**: Running `frappe-cli config set` with no arguments prompts for input.

---

### User Story 6 - Disable SSL Verification (Priority: P2)

As a CLI user, I want to bypass SSL certificate validation using a `--no-verify` option, so that I can connect to local development sites with self-signed or invalid certificates.

**Independent Test**: Running commands against a site with self-signed certificates with `--no-verify` succeeds rather than throwing SSL validation errors.

---

## Edge Cases

- **Connection Timeout / Network Down**: If the remote site is unreachable, the CLI must exit cleanly with a clear network timeout message and a non-zero exit code, instead of showing a Python stack trace.
- **Unauthorized (401/403) Access**: If the stored keys are invalid or expired, the CLI must report that authentication failed and instruct the user to re-configure credentials.
- **Method Not Found (404) / Method Not Whitelisted**: If the called function does not exist or isn't whitelisted on the remote site, the CLI must output the remote server error message.
- **Missing Selected Profile**: If a user selects a profile via `--profile` that is not configured, the CLI must exit with a clean error message and code `2`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: CLI MUST allow configuring remote site connection details (URL, API keys).
- **FR-002**: CLI MUST authenticate remote requests using credentials (API Key and API Secret) stored locally in a JSON configuration file (`~/.frappe-cli.json`) under the user's home directory.
- **FR-003**: CLI MUST support both remote method invocation (via `frappe.call` RPC calls) and standard DocType CRUD operations (GET/POST/PUT/DELETE) on remote site records.
- **FR-004**: CLI MUST display responses in raw JSON format by default, with an optional `-t` / `--table` toggle flag to print formatted human-readable ASCII tables.
- **FR-005**: CLI MUST handle errors gracefully by printing clean error messages to stderr and returning a non-zero exit code.
- **FR-006**: CLI MUST support multiple site profiles stored in `~/.frappe-cli.json` and switching the default profile via `config use <profile_name>`.
- **FR-007**: CLI MUST accept a global `--profile <name>` option to execute commands against a specific profile without changing the default.
- **FR-008**: CLI MUST prompt the user interactively for `site_url`, `api_key`, and `api_secret` in the `config set` command if they are not provided via command line options.
- **FR-009**: CLI MUST support storing a SSL verification setting (`verify`) per profile and overriding it globally via a `--no-verify` flag.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully configure connection credentials in under 1 minute.
- **SC-002**: CLI executes commands and displays remote server outputs in less than 2 seconds under normal network latency (<100ms).
- **SC-003**: 100% of connection failures, timeout, or authentication issues result in structured, human-readable instructions instead of system tracebacks.
- **SC-004**: Users can list, use, and switch between at least 5 different site profiles without configuration pollution.

## Assumptions

- The remote Frappe site has API access enabled and the target server functions are whitelisted (`@frappe.whitelist()`).
- The developer has Python 3.8+ and standard dependencies installed.
- Click is the chosen CLI framework.
- Local configuration is stored in the user's home directory.
