# frappe-remote-cli

[![PyPI version](https://img.shields.io/pypi/v/frappe-remote-cli.svg)](https://pypi.org/project/frappe-remote-cli/)
[![Python](https://img.shields.io/pypi/pyversions/frappe-remote-cli.svg)](https://pypi.org/project/frappe-remote-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-131%20passing-brightgreen.svg)](#running-tests)

```
  ███████╗██████╗  █████╗ ██████╗ ██████╗ ███████╗     ██████╗██╗     ██╗
  ██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔════╝    ██╔════╝██║     ██║
  █████╗  ██████╔╝███████║██████╔╝██████╔╝█████╗      ██║     ██║     ██║
  ██╔══╝  ██╔══██╗██╔══██║██╔═══╝ ██╔═══╝ ██╔══╝      ██║     ██║     ██║
  ██║     ██║  ██║██║  ██║██║     ██║     ███████╗    ╚██████╗███████╗██║
  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝     ╚══════╝     ╚═════╝╚══════╝╚═╝

                     Frappe Remote CLI  ·  frappe-cli  ·  v0.1.7
              Query · Format · Merge · Automate — all via REST & MCP
```

**A professional, feature-rich Python CLI and Model Context Protocol (MCP) server to query, inspect, and update remote [Frappe](https://frappeframework.com/) sites directly from the terminal or your favorite AI agent.**

Built with Python, [Click](https://click.palletsprojects.com/), [Requests](https://requests.readthedocs.io/), and [Tabulate](https://pypi.org/project/tabulate/). Fully isolated, robustly tested, and developer-friendly.

---

## Two Interfaces in One

```
┌─────────────────────────────────────────────────────────────────────┐
│                          frappe-cli                                 │
├──────────────────────────────┬──────────────────────────────────────┤
│   💻  TERMINAL CLI COMMANDS  │   🤖  MODEL CONTEXT PROTOCOL (MCP)   │
│                              │                                      │
│  config set/show/use/remove  │  doc_list / doc_get / doc_count      │
│  doc list/get/create/delete  │  get_schema / run_report / call_method│
│  doc count                   │  bulk_create / bulk_update / bulk_del│
│  bulk create/update/delete   │  stdio / background HTTP daemon      │
│  schema <doctype>            │  exposes all remote site tools to LLMs│
│  report <name>               │  seamless Cursor/Claude integration  │
└──────────────────────────────┴──────────────────────────────────────┘
```

---

## Highlights

- **Multi-Profile Configuration Manager:** Securely store connection credentials for multiple remote sites in `~/.frappe-cli.json` (enforced with strict `0600` file permissions).
- **Regional Formatting Engine:** Automatically formats date strings (`us`, `french`, `german`, `plain`) and float cells in terminal output tables on-the-fly.
- **Dynamic 3-Pass Schema Resolution:** Fetches standard fields, splices in Custom Fields at their correct layout indices, and overrides Select dropdown choices using `Property Setter` data directly from the live database.
- **Sequential Client-Side Bulk Actions:** Automate imports and mass deletions using JSON inline strings or `@filepath` references, featuring real-time spinner feedback and success tables.
- **Desk Reports in Terminal:** Run server-side SQL query or script reports, zip matching columns, and output clean formatted tables.
- **Built-in PyPI Update Checker:** Automatically checks for library upgrades once a day in the background, printing helpful upgrade instructions without slowing down commands.
- **Full Model Context Protocol (MCP) Server:** Exposes 15 tools to AI coding agents (Claude Desktop, Cursor, etc.) via stdio or a detached HTTP/SSE background daemon.

---

## Installation

### Globally via [uv](https://github.com/astral-sh/uv) (Recommended)
```bash
# Install tool globally
uv tool install frappe-remote-cli

# Verify installation
frappe-cli --help
```

### Globally via `pipx` or standard `pip`
```bash
# Using pipx
pipx install frappe-remote-cli

# Using standard pip
pip install --user frappe-remote-cli
```

### Local Development
To set up a local virtual environment for development or custom builds:
```bash
git clone https://github.com/vanbaopham160-clnp/frappe-remote-cli.git
cd frappe-remote-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## Configuration

```bash
# Set up a new profile (prompts interactively for missing arguments)
frappe-cli config set --profile dev

# Set configuration with specific regional formatting layouts
frappe-cli config set \
  --site-url "https://my-frappe-site.com" \
  --api-key "ab12cd34ef56" \
  --api-secret "gh78ij90kl12" \
  --date-format french \
  --number-format german \
  --profile production

# List all configured profiles
frappe-cli config list

# Select default profile
frappe-cli config use staging

# Show configuration details (prints text, JSON, or YAML)
frappe-cli config show
frappe-cli config show --format json
frappe-cli config show --format yaml

# Verify remote site connection diagnostic
frappe-cli config check

# Remove a connection profile
frappe-cli config remove production
```

**Supported Date Formats:** `plain` (ISO default), `us` (`MM/DD/YYYY`), `french` (`DD/MM/YYYY`), `german` (`DD.MM.YYYY`)  
**Supported Number Formats:** `plain` (`1234567.89`), `us` (`1,234,567.89`), `french` (`1 234 567,89`), `german` (`1.234.567,89`)

---

## Usage Guide

### 1. Document CRUD Commands (`doc`)
Perform operations on individual document records. Toggle table output with `--table` / `-t`.

```bash
# List documents with filtering, field subsetting, and sorting
frappe-cli doc list Customer --fields "name,customer_name,creation" --table

# Get document count matching filters
frappe-cli doc count Customer -q '[["disabled", "=", "0"]]'

# Fetch specific document detail
frappe-cli doc get Customer CUST-0001 --table

# Create a new document record
frappe-cli doc create Customer -d '{"customer_name": "Alice", "customer_type": "Individual"}'

# Update fields on a document
frappe-cli doc update Customer CUST-0001 -d '{"phone": "+1234567890"}'

# Delete a document record
frappe-cli doc delete Customer CUST-0001
```

### 2. Client-Side Bulk Operations (`bulk`)
Create, update, or delete batches of documents sequentially with progress spinners.

```bash
# Bulk create from inline JSON
frappe-cli bulk create ToDo -d '[
  {"description": "Task A", "priority": "High"},
  {"description": "Task B", "priority": "Medium"}
]'

# Bulk create from a local JSON file path
frappe-cli bulk create ToDo -d @tasks.json

# Bulk update (each record must contain the 'name' field)
frappe-cli bulk update ToDo -d @updates.json

# Bulk delete by list of document names
frappe-cli bulk delete ToDo --names '["TD-0001", "TD-0002"]'
```

### 3. Server Reports Execution (`report`)
Execute whitelisted Frappe query or script reports.

```bash
# Run report with multiple key-value parameters and output table
frappe-cli report "Accounts Payable" \
  -p company "My Company" \
  -p report_date "2026-05-31" \
  --table
```

### 4. Live Schema Introspection (`schema`)
Query the live merged fields dictionary of a DocType.

```bash
# Display formatted fields schema table (standard + custom fields + property setters)
frappe-cli schema Customer --table

# Output complete raw JSON schema response
frappe-cli schema Customer --full
```

### 5. Remote RPC Execution (`call`)
Invoke whitelisted Python method APIs on the site:
```bash
frappe-cli call frappe.auth.get_logged_user --table
frappe-cli call my_app.api.calculate -p a 10 -p b 20
```

### 6. CLI Self-Upgrade (`update`)
Check for package updates and upgrade the local installation directly in place:
```bash
# Check if a new version is available on PyPI
frappe-cli update --check

# Upgrade the CLI to the latest version immediately (without confirmation prompt)
frappe-cli update --yes
```

---

## Model Context Protocol (MCP) Server Setup

Bridge your Frappe sites to LLM environments seamlessly.

### Stdio Transport Mode (Claude Desktop, Cursor)
Expose tools via standard input/output. Add the following to your `claude_desktop_config.json`:

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

### Detached HTTP Daemon Mode
Run a persistent server in the background for remote HTTP SSE clients:

```bash
# Start background server daemon on port 8765
frappe-cli mcp start --transport http --port 8765 --detach

# Check daemon PID, port, logs, and uptime
frappe-cli mcp status

# Shut down the background process group cleanly
frappe-cli mcp stop
```

*Daemon configuration and pid states are written to `~/.config/frappe-cli/mcp.json`.*

---

## Running Tests

Run the full pytest suite (unit tests + request mocking):
```bash
# Run all tests
pytest

# Verbose test runner
pytest -v
```
