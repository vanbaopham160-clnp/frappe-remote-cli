# Research & Decisions: Extended Features and MCP Server

This document outlines the technical research, architectural decisions, and alternatives considered for implementing the advanced queries, metadata listings, bulk actions, and MCP server features.

---

## 1. Regional Date & Number Formatting

### Decision
Implement custom string parsing and formatting utilities in Python using the native `datetime` library and basic string manipulation, rather than bringing in heavy external localization libraries (such as Babel).

### Rationale
- Minimizes external dependency weight to keep `frappe-remote-cli` lightweight.
- The formatting requirements are highly specific: four date layouts (`yyyy-mm-dd`, `dd-mm-yyyy`, `dd/mm/yyyy`, `mm/dd/yyyy`) and four number layouts (`french`, `us`, `german`, `plain`). These are easily mapped using python's `datetime.strftime` and string replacements.
- Cell value formatting will be integrated directly into the print/output layer (in `formatter.py`).

### Alternatives Considered
- **Babel**: Rejected because it increases package size and adds unnecessary complexity for a fixed subset of formats.

---

## 2. Dynamic Schema Resolution (Merging Fields)

### Decision
Perform client-side multi-pass REST queries to fetch the base `DocType` schema, then query `/api/resource/Custom Field` and `/api/resource/Property Setter` resources to merge them in memory.

### Rationale
- The standard `/api/resource/DocType/<name>` endpoint only returns fields defined in the codebase.
- Customizations made via the Frappe Desk UI are stored in `Custom Field` and `Property Setter` doctypes on the server.
- Splicing custom fields in-place after their `insert_after` target, and overriding select dropdown `options` via property setters, provides an accurate schema representation.
- The CLI credentials must have read access to these doctypes. If they don't, the CLI will gracefully fall back to the base schema and print a warning to stderr.

### Alternatives Considered
- **Server-side Whitelisted Method**: Rejected because it would require installing a custom Frappe application on the target server. The CLI must be fully compatible with stock remote Frappe instances.

---

## 3. Client-Side Bulk Operations

### Decision
Implement bulk actions (`bulk create`, `bulk update`, `bulk delete`) as client-side loops in the CLI. The command processes items sequentially, catches exceptions per item, and shows real-time progress via stdout or a spinner.

### Rationale
- Sequentially processing REST requests avoids overloading the remote server.
- Allows the CLI to report precise success/failure logs for each individual item index.
- Provides robust client-side control and error handling.

### Alternatives Considered
- **Frappe Bulk REST API**: Rejected. Frappe has an internal RPC endpoint for bulk operations, but its error handling is opaque (failing the entire batch or hiding traceback details), and it is not universally whitelisted on all Frappe versions. Sequential client-side loops offer superior developer feedback.

---

## 4. Model Context Protocol (MCP) Server Integration

### Decision
Use the official Python MCP SDK (`mcp` library) to implement the stdio and HTTP JSON-RPC servers.

### Rationale
- The official SDK implements the protocol spec correctly, handling schemas, tool registrations, and request/response serialization out of the box.
- Integrates seamlessly with python async loops.

### Alternatives Considered
- **Custom JSON-RPC parser**: Rejected. Re-implementing the protocol is error-prone and does not scale well as the MCP specification evolves.

---

## 5. Background Daemonization for HTTP MCP Mode

### Decision
On Unix systems, daemonize the background MCP server by spawning the CLI in a separate process using `subprocess.Popen` with `start_new_session=True` (or `preexec_fn=os.setsid` for older Python versions). On Windows, use `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP`. Write PID, port, site/profile, start timestamp, and log path to a state file `~/.config/frappe-cli/mcp.json`.

### Rationale
- `start_new_session=True` detaches the child process from the parent terminal session, allowing it to continue running after the user closes their terminal.
- Saving state to a JSON file allows other CLI instances (`mcp status`, `mcp stop`) to query and stop the daemon easily using standard OS signals (`SIGTERM`).

### Alternatives Considered
- **External Daemon Tools (systemd, launchd, pm2)**: Rejected because it makes setup platform-dependent and requires administrative privileges. Implementing self-daemonization inside the CLI is simple and cross-platform.
