# Frappe Remote CLI Tool

A Python command-line utility built with Click and Requests to communicate with a remote Frappe site (v15).

## Features

- **Local Configuration**: Securely store connection URLs and API credentials locally in `~/.frappe-cli.json` (permissions enforced at `0600`). Supports multiple site profiles.
- **Regional Formatting**: Output dates and numbers in locale-specific formats — US, French, German, or plain ISO.
- **Interactive Prompts**: Prompts you for configuration parameters when setting up connection configs if options are omitted.
- **SSL Verification Control**: Bypass SSL certificate validation using the `--no-verify` option for local or development environments.
- **Remote RPC Executions**: Call any remote whitelisted Python methods on the site via `frappe.call`.
- **REST DocType CRUD**: Query, fetch, insert, update, or delete DocType records using clean subcommand interfaces.
- **Document Count**: Count documents matching any filter set without fetching all records.
- **Bulk Operations**: Create, update, or delete multiple documents in a single command call with a progress summary table.
- **Metadata Listings**: List all available DocTypes or Reports visible to the current user.
- **Report Execution**: Run Frappe query or script reports by name with optional filter parameters.
- **Dynamic Schema Resolution**: Fetch the fully merged field schema for any DocType — base fields, custom fields, and property setter overrides — in a single command.
- **MCP Server**: Expose all CLI operations as native Model Context Protocol (MCP) tools for AI agent integration — via stdio or a detached HTTP daemon.
- **Rich Formatting**: Display API responses in raw JSON format by default (ideal for scripting/piping), with an optional `-t` / `--table` toggle flag to print formatted human-readable ASCII tables.
- **Robust Exception Handling**: Clean terminal error formatting without raw stack traces.

---

## Installation

Ensure you have Python 3.10+ installed.

### Global Installation (Recommended)
The easiest way to run the CLI globally is using [uv](https://github.com/astral-sh/uv) or [pipx](https://github.com/pypa/pipx):

```bash
# Install with uv
uv tool install frappe-remote-cli

# Or install with pipx
pipx install frappe-remote-cli
```

Alternatively, you can install it using standard `pip`:
```bash
pip install frappe-remote-cli
```

### For Local Development
If you want to modify or contribute to the codebase:
1. Clone this repository.
2. Initialize virtual environment and install dependencies in editable mode:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## Usage

Verify the CLI is registered in your path:

```bash
frappe-cli --help
```

### Global Options

You can specify these options before any subcommand:
- `--profile <name>`: Run the command against a specific profile configuration.
- `--no-verify`: Disable SSL certificate verification (useful for self-signed certificates).

---

### 1. Configuration Setup

```bash
# Set connection parameters (prompts interactively for missing arguments)
frappe-cli config set \
  --site-url "https://my-frappe-site.com" \
  --api-key "ab12cd34ef56" \
  --api-secret "gh78ij90kl12" \
  --profile production

# Set connection with regional formatting preferences
frappe-cli config set \
  --site-url "https://my-frappe-site.com" \
  --api-key "ab12cd34ef56" \
  --api-secret "gh78ij90kl12" \
  --date-format french \
  --number-format german

# List all configured profiles
frappe-cli config list

# Switch default profile
frappe-cli config use staging

# Inspect active profile (text, json, or yaml output)
frappe-cli config show
frappe-cli config show --format json
frappe-cli config show --format yaml

# Remove a profile
frappe-cli config remove staging

# Run connection diagnostic for active profile
frappe-cli config check
```

**Supported format values**: `plain` (ISO default), `us`, `french`, `german`

---

### 2. Method Execution (`call`)

Trigger any remote method decorated with `@frappe.whitelist()`:

```bash
# Check logged-in user
frappe-cli call frappe.auth.get_logged_user

# Execute method with key-value parameters
frappe-cli call my_app.api.add -p a 10 -p b 20

# Format output as table instead of default JSON
frappe-cli call frappe.auth.get_logged_user --table
```

---

### 3. Document CRUD (`doc`)

#### List records:
```bash
frappe-cli doc list Customer --fields "name,customer_name,creation" --table
```

#### Count records:
```bash
# Count all customers
frappe-cli doc count Customer

# Count with filters
frappe-cli doc count Customer -q '[["disabled","=","0"]]'
```

#### Get record:
```bash
frappe-cli doc get Customer CUST-0001 --table
```

#### Create record:
```bash
frappe-cli doc create Customer -d '{"customer_name": "Alice", "customer_type": "Individual"}'
```

#### Update record:
```bash
frappe-cli doc update Customer CUST-0001 -d '{"phone": "+1234567890"}'
```

#### Delete record:
```bash
frappe-cli doc delete Customer CUST-0001
```

---

### 4. Bulk Operations (`bulk`)

Operate on multiple documents in a single call. Results are displayed as a summary table with per-record status.

```bash
# Bulk create from a JSON array
frappe-cli bulk create Customer -d '[
  {"customer_name": "Alice", "customer_type": "Individual"},
  {"customer_name": "Bob", "customer_type": "Company"}
]'

# Bulk create from a JSON file
frappe-cli bulk create Customer -d @customers.json

# Bulk update (each record must include 'name')
frappe-cli bulk update Customer -d '[
  {"name": "CUST-0001", "phone": "123"},
  {"name": "CUST-0002", "phone": "456"}
]'

# Bulk delete by name list
frappe-cli bulk delete Customer -n '["CUST-0001", "CUST-0002"]'
frappe-cli bulk delete Customer -n @names.json
```

---

### 5. Metadata (`meta`)

```bash
# List all DocTypes
frappe-cli meta doctypes --table

# List with filters
frappe-cli meta doctypes -q '[["module","=","Selling"]]' --table

# List all Reports
frappe-cli meta reports --table
```

---

### 6. Report Execution (`report`)

```bash
# Run a report (JSON output by default)
frappe-cli report "General Ledger"

# Run with filters and show as table
frappe-cli report "Sales Order Summary" -p company "My Company" --table

# Multiple filter parameters
frappe-cli report "Accounts Payable" \
  -p company "My Company" \
  -p report_date "2024-12-31" \
  --table
```

---

### 7. Schema Resolution (`schema`)

Fetch the merged schema for a DocType — base fields, custom fields (injected at their correct positions), and Property Setter overrides (e.g. Select option changes) — all in one command.

```bash
# Compact view (default): key field attributes only
frappe-cli schema Customer --table

# Full view: all field attributes
frappe-cli schema Customer --full --table

# JSON output for scripting
frappe-cli schema Customer
```

---

### 8. MCP Server

Expose all CLI operations as [Model Context Protocol](https://modelcontextprotocol.io) tools for use with AI assistants (e.g. Claude Desktop, Cursor, etc.).

#### Available MCP Tools (15):
`doc_list`, `doc_get`, `doc_create`, `doc_update`, `doc_delete`, `doc_count`, `call`, `meta_doctypes`, `meta_reports`, `run_report`, `get_schema`, `bulk_create`, `bulk_update`, `bulk_delete`, `check_connection`

#### Stdio transport (for AI agent integration):
```bash
# Start MCP server on stdio (blocking — used by AI assistants directly)
frappe-cli mcp start
frappe-cli mcp start --transport stdio
```

Example MCP config for Claude Desktop (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "frappe": {
      "command": "frappe-cli",
      "args": ["mcp", "start"]
    }
  }
}
```

#### HTTP daemon transport:
```bash
# Start as a background HTTP daemon (port 8765 by default)
frappe-cli mcp start --transport http --detach

# Check daemon status
frappe-cli mcp status

# Stop the daemon
frappe-cli mcp stop
```

Daemon state is persisted to `~/.config/frappe-cli/mcp.json`.

---

## Running Tests

Run the full test suite (unit + integration):

```bash
pytest

# Unit tests only
pytest tests/unit/

# With verbose output
pytest -v
```

---

## Configuration File Format

The config file is stored at `~/.frappe-cli.json`:

```json
{
  "default_profile": "production",
  "profiles": {
    "production": {
      "site_url": "https://my-frappe-site.com",
      "api_key": "...",
      "api_secret": "...",
      "verify": true,
      "date_format": "french",
      "number_format": "german"
    },
    "staging": {
      "site_url": "https://staging.my-frappe-site.com",
      "api_key": "...",
      "api_secret": "...",
      "verify": false
    }
  }
}
```
