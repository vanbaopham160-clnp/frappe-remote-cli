# CLI Commands Contract

This contract defines the exact commands, subcommands, options, and flags introduced or updated by this feature in the `frappe-cli` command-line application.

---

## 1. Global Flags
Available on all commands:
- `--profile <name>`: Switch the connection profile. Defaults to the `default_profile` configured in `.frappe-cli.json`.
- `--config <path>`: Override the default configuration JSON file path.
- `--no-verify`: Disable SSL certificate validation for HTTPS requests.
- `--json` / `-j`: Output raw JSON instead of tables.

---

## 2. Configuration Subcommands (`frappe-cli config ...`)

### `config set`
Updates connection profile credentials and regional formats.
- **Flags**:
  - `--site-url <url>` (prompted if missing)
  - `--api-key <key>` (prompted if missing)
  - `--api-secret <secret>` (prompted if missing; hidden in prompts)
  - `--profile <name>` (defaults to `default`)
  - `--verify/--no-verify` (defaults to `--verify`)
  - `--number-format <french|us|german|plain>` (optional)
  - `--date-format <yyyy-mm-dd|dd-mm-yyyy|dd/mm/yyyy|mm/dd/yyyy>` (optional)

### `config show`
Prints active profile settings. Secret keys are masked in table outputs.
- **Flags**:
  - `--json` / `-j`: Outputs as raw JSON.
  - `--yaml` / `-y`: Outputs as raw YAML.

### `config list`
Lists all profiles configured in the configuration file. Default profile is marked with an asterisk (`*`).

### `config use <profile_name>`
Sets the default profile name.
- **Arguments**:
  - `<profile_name>` (required)

### `config remove <profile_name>`
Deletes a profile from the configuration file.
- **Arguments**:
  - `<profile_name>` (required)
- **Flags**:
  - `--yes` / `-y`: Skip the deletion confirmation prompt.

---

## 3. Data Query & CRUD Commands

### `doc list <doctype>`
List documents of a doctype.
- **Arguments**:
  - `<doctype>` (required)
- **Flags**:
  - `--fields` / `-f` (comma-separated or JSON list of fieldnames; defaults to `name`)
  - `--filters` / `-q` (JSON object filter e.g. `{"status":"Open"}` or JSON array list)
  - `--limit` / `-l` (max records to return, defaults to 20)
  - `--order-by` / `-o` (sorting expression, e.g. `creation desc`)
  - `--table` / `-t`: Forces pretty table output.

### `doc get <doctype> [name]`
Fetch a document's details. If `<name>` is omitted and `<doctype>` is a Single DocType, name defaults to `<doctype>`.
- **Arguments**:
  - `<doctype>` (required)
  - `[name]` (optional)
- **Flags**:
  - `--fields` / `-f` (CSV or JSON list of fields to include)
  - `--keys` (comma-separated keys to keep in JSON output mode)
  - `--table` / `-t`: Force table output.

### `doc count <doctype>`
Print the integer count of documents matching the filter.
- **Arguments**:
  - `<doctype>` (required)
- **Flags**:
  - `--filters` / `-q` (JSON object/list filters)

### `doc delete <doctype> <name>`
Delete a document.
- **Arguments**:
  - `<doctype>` (required)
  - `<name>` (required)
- **Flags**:
  - `--yes` / `-y`: Bypass interactive confirmation.

---

## 4. Bulk Subcommands (`frappe-cli bulk ...`)

### `bulk create <doctype>`
Creates documents in bulk.
- **Arguments**:
  - `<doctype>` (required)
- **Flags**:
  - `--data` / `-d` (JSON array of field dictionaries)
  - `--file` / `-f` (JSON file containing array of field dictionaries)
  *One of `--data` or `--file` must be provided.*

### `bulk update <doctype>`
Updates documents in bulk.
- **Arguments**:
  - `<doctype>` (required)
- **Flags**:
  - `--data` / `-d` (JSON array of dicts; each MUST have a `"name"` key)
  - `--file` / `-f` (JSON file containing array of dicts; each MUST have a `"name"` key)
  *One of `--data` or `--file` must be provided.*

### `bulk delete <doctype>`
Deletes documents in bulk.
- **Arguments**:
  - `<doctype>` (required)
- **Flags**:
  - `--names` (comma-separated list of document names to delete)
  - `--file` / `-f` (JSON file containing a list of document name strings)
  - `--yes` / `-y`: Bypass interactive confirmation prompt.
  *One of `--names` or `--file` must be provided.*

---

## 5. System Metadata & Reporting

### `schema <doctype>`
Displays field definitions of a doctype, integrating base schema, custom fields, and option overrides.
- **Arguments**:
  - `<doctype>` (required)
- **Flags**:
  - `--full`: Returns complete raw response, JSON mode only.
  - `--keys`: Comma-separated top-level keys to filter, JSON mode only.

### `meta doctypes`
Lists available doctypes.
- **Flags**:
  - `--module` / `-m` (filter by module name)
  - `--limit` / `-l` (defaults to 50)

### `meta reports`
Lists available query and script reports.
- **Flags**:
  - `--module` / `-m` (filter by module name)
  - `--limit` / `-l` (defaults to 50)

### `report <report_name>`
Runs a query report and renders results as a table.
- **Arguments**:
  - `<report_name>` (required)
- **Flags**:
  - `--filters` (JSON string of report filter arguments)
  - `--limit` / `-l` (limit row lines printed)
  - `--keys` (comma-separated keys to keep in JSON output mode)

---

## 6. Model Context Protocol (`frappe-cli mcp ...`)

### `mcp`
Starts an MCP server. Defaults to running an interactive stdio server.
- **Flags**:
  - `--detach` / `-d`: Starts the MCP server as a detached background HTTP daemon.
  - `--port` / `-p`: Daemon port number (defaults to 8765).

### `mcp status`
Displays background daemon running status, PID, port, started timestamp, and log file path.

### `mcp stop`
Terminates the detached background server.
