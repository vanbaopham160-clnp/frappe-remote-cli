# Feature Specification: Extended Features and MCP Server

**Feature Branch**: `002-extended-cli-features`  
**Created**: 2026-05-28  
**Status**: Draft  
**Input**: User description: "Update remote CLI with advanced query, reporting, bulk, and metadata tools, plus native Model Context Protocol (MCP) integration, excluding custom authentication flows."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Localized Formatting & Metadata Retrieval (Priority: P1)

Users want to query remote doctypes, retrieve matching records, count documents matching specific filters, and view standard lists of available desk reports and doctypes. They require date and numeric fields to be formatted automatically according to their local regional preferences rather than plain raw server formats.

**Why this priority**: Highly critical for basic readability and configuration. Proper regional representation prevents decimal errors and mismatching date formats, while metadata listings are essential for remote discovery.

**Independent Test**: Fetch a list of records or count records on a remote doctype, and list available doctypes or reports. Verify dates and numbers are formatted according to configured preferences (e.g. European numbering `1 000 000,00` and date format `DD/MM/YYYY`).

**Acceptance Scenarios**:

1. **Given** the CLI is configured with European number format and slash date format, **When** listing documents that contain numeric totals and creation timestamps, **Then** numbers display with space group separators and commas for decimals, and dates display as `DD/MM/YYYY`.
2. **Given** a remote doctype exists, **When** checking its record count using the count command with a filter, **Then** the terminal prints the exact integer count matching the filters.
3. **Given** the user needs to inspect the system configuration, **When** running commands to list doctypes or desk reports, **Then** a structured table of names and associated modules is displayed in the terminal.

---

### User Story 2 - Desk Report Execution (Priority: P1)

Users want to execute whitelisted desk query reports on the remote server directly from the command line and display the resulting data rows formatted as a table, utilizing report filters and preserving column mappings.

**Why this priority**: Desk reports aggregate data (e.g. Accounts Receivable) on the server, which cannot easily be compiled client-side. Exposing report runs in the CLI saves significant developer time.

**Independent Test**: Run a report by name, providing filter parameters, and verify columns and data cells match expected outcomes.

**Acceptance Scenarios**:

1. **Given** a standard query report exists on the server, **When** executing it via the CLI by specifying its name and a JSON string of filters, **Then** the CLI queries the remote endpoint, processes column names, aligns cell values correctly, and outputs a formatted table.
2. **Given** a query report returns rows in either a zipped array format or direct object key-value format, **When** the report is executed, **Then** the CLI parses both response structures seamlessly and displays standard aligned tables.

---

### User Story 3 - Dynamic Schema Resolution (Priority: P1)

Users want to see the accurate schema definition of a doctype, including standard fields, custom fields (spliced in their correct locations), and field option overrides (property setters) customized dynamically on the remote server.

**Why this priority**: Standard doctype definitions stored in code repositories do not reflect customizations made on the live database (e.g. Custom Fields or modified dropdown options). AI tools and developers need live, resolved schemas to avoid referencing obsolete or missing fields.

**Independent Test**: Fetch a doctype schema and verify that standard fields, custom fields (resolved from the separate Custom Field table), and select options (resolved from Property Setters) are merged into a single integrated schema definition.

**Acceptance Scenarios**:

1. **Given** a doctype has custom fields appended after standard fields, **When** fetching the schema via the CLI, **Then** the CLI performs a multi-pass fetch to query base fields, resolve custom fields, place them in the correct `insert_after` indexes, and outputs the merged list.
2. **Given** a field's options have been customized using a property setter, **When** requesting the schema, **Then** the CLI resolves property setters for the doctype, overrides the base options, and outputs the updated dropdown choice values.

---

### User Story 4 - Client-Side Bulk Actions (Priority: P2)

Users want to create, update, or delete multiple records in a single command using a local JSON array or JSON file, with visual progress updates and a final success/failure summary table.

**Why this priority**: Eliminates the overhead of scripting multiple individual CRUD commands manually.

**Independent Test**: Execute a bulk-create, bulk-update, or bulk-delete action on a list of items and check the final table output for success status.

**Acceptance Scenarios**:

1. **Given** a JSON file containing an array of three document payloads, **When** running bulk create, **Then** the CLI processes each item sequentially, displays a progress indicator (such as an in-progress spinner for each row index), and prints a summary table showing created name IDs and status messages.
2. **Given** a list of document names, **When** running bulk delete, **Then** the CLI attempts to delete each document and outputs a table listing the deletion outcome for each document, returning a non-zero exit status if any deletion failed.

---

### User Story 5 - Model Context Protocol (MCP) Integration (Priority: P2)

Users want to run an MCP server through the CLI to expose all CLI capabilities (record queries, schema fetching, custom methods, report execution, and bulk actions) as native tools for AI coding assistants.

**Why this priority**: Essential for integrating the CLI with modern AI IDEs (Cursor, Claude Code, etc.), letting coding agents inspect and manipulate live site resources autonomously.

**Independent Test**: Run the MCP command in stdio mode and perform a protocol handshake, or run it in background mode and check its status.

**Acceptance Scenarios**:

1. **Given** an AI agent starts the CLI in stdio MCP mode, **When** sending JSON-RPC requests, **Then** the CLI server responds on stdout with standard MCP tool definitions matching the CLI's capabilities.
2. **Given** the user wants a persistent connection, **When** starting the MCP server in background/detached mode, **Then** the CLI daemonizes the process, writes its status (PID, port, active site, logs) to a local JSON state file, and allows clean shutdown via a stop command.

---

### Edge Cases

- **Mismatched Report Columns**: What happens when a query report definition lists columns but returns row structures that contain fewer values? The CLI must pad the rows with empty values or display place-marker symbols rather than throwing index out of bounds exceptions.
- **Dynamic Field Splicing Orphans**: If a custom field specifies an `insert_after` target that does not exist in the base schema, it must be gracefully appended to the very end of the fields collection.
- **Port Conflict in Background Daemon**: If starting the background HTTP MCP server on a port that is already in use, the command must exit cleanly with an error message and clean up any partial state files.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The CLI MUST support a configuration menu to set and persist default formatting options, including regional number formats (French, US, German, Plain) and date formats (ISO, European-dash, European-slash, US-slash).
- **FR-002**: The CLI MUST automatically parse and apply number and date formatting configurations to all float/date columns printed in terminal tables.
- **FR-003**: The CLI MUST support metadata listing commands for listing available desk reports (`list-reports`), listing system doctypes (`list-doctypes`), and counting records matching filters (`count-docs`).
- **FR-004**: The CLI MUST support a report execution command (`run-report`) that queries query-report endpoints, parses the response (including array-of-arrays or array-of-objects structure), and outputs an aligned table.
- **FR-005**: The CLI MUST support a schema retrieval command (`get-schema`) that dynamically resolves live site doctype configurations by merging Custom Field records and Property Setter overrides in-place.
- **FR-006**: The CLI MUST support client-side bulk operations (`bulk-create`, `bulk-update`, `bulk-delete`) with user progress feedback (spinners/line counts) and a final success/failure summary table.
- **FR-007**: The CLI MUST include an MCP command (`mcp`) implementing the Model Context Protocol to expose all commands as JSON-RPC tools.
- **FR-008**: The MCP server MUST support a standard input/output (stdio) channel.
- **FR-009**: The MCP server MUST support a background/detached HTTP mode, writing process details (PID, port, logs) to a state file (`mcp.json`), and offering control subcommands (`status`, `stop`) to manage the background daemon process group.

### Key Entities *(include if feature involves data)*

- **Regional Format Settings**: Represents formatting rules for parsing/displaying dates and floats.
  - Attributes: `number_format` (enum), `date_format` (enum).
- **Merged DocType Schema**: Represents a dynamically synthesized database schema.
  - Attributes: `name` (string), `fields` (list of standard and custom fields merged sequentially), `field_overrides` (property setters mapped to standard fields).
- **Desk Report Matrix**: Represents tabular results from a report run.
  - Attributes: `columns` (list of labels/types), `result` (list of lists or list of dicts).
- **MCP Daemon State**: Represents background process metadata.
  - Attributes: `pid` (int), `port` (int), `started_at` (timestamp), `site` (string), `log_path` (string).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can execute desk reports and see formatted columns aligned in the terminal in under 2 seconds.
- **SC-002**: When running `get-schema`, custom fields and option overrides are successfully resolved and merged in-place within a single CLI query pass.
- **SC-003**: Bulk operations can process up to 100 documents sequentially, displaying a real-time progress index spinner per row, and returning a zero exit code if and only if all items succeeded.
- **SC-004**: In background MCP daemon mode, the server can be detached, queried for status, and cleanly terminated with `stop`, leaving no orphaned child processes running.

## Assumptions

- **Existing Client Connection**: The CLI will reuse the existing connection profiles and client request sessions established in the current configuration.
- **Custom Field and Property Setter Access**: The API credentials used by the CLI have sufficient read permissions on the remote site to query both `Custom Field` and `Property Setter` doctypes.
- **No Custom Authentication**: Interactive OAuth registration, PKCE authorization code handshakes, and automatic token refresh mechanisms are out of scope for this spec.
- **Local Web Server**: The background MCP HTTP transport runs on localhost and does not require SSL or external reverse proxies.
