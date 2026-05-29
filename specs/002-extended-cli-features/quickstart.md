# Quickstart Guide: Extended Features and MCP Server

This guide provides examples for utilizing regional formatting settings, document counting, dynamic schemas, reporting, bulk execution, and the Model Context Protocol (MCP) server features.

---

## 1. Regional Formatting Settings

Configure your preferences for how date and number values should display when querying remote sites:

```bash
# Setup numbers to use US formatting and dates to use European slash layout
frappe-cli config set --number-format us --date-format dd/mm/yyyy
```

Verify the config show output:
```bash
frappe-cli config show
# Output will display the verified formats, and all subsequent `doc list` or `doc get`
# commands will format dates and float numbers automatically.
```

---

## 2. Document Counting

Count documents of a specified DocType matching any given filter constraints without pulling down the full datasets:

```bash
# Count total number of User documents
frappe-cli doc count User

# Count documents with specific filter criteria
frappe-cli doc count ToDo --filters '[["status", "=", "Open"]]'
```

---

## 3. Dynamic Schema Retrieval

Examine the full, live database schema of a doctype, including customized standard fields, property setters, and custom fields spliced in their database order:

```bash
# Display schema fields as a structured table
frappe-cli schema "Sales Invoice" --table

# Output schema as JSON
frappe-cli schema "Sales Invoice"
```

---

## 4. Query Reports Execution

Execute server-side reports and view the results in the terminal:

```bash
# Run a financial report with parameters and view as a formatted table
frappe-cli report "General Ledger" -p company "My Company" -p from_date "2026-01-01" --table
```

---

## 5. Bulk Creation and Deletion

Perform bulk CRUD actions from local JSON payloads:

```bash
# Create multiple ToDo documents from inline data
frappe-cli bulk create ToDo --data '[{"description":"Review MR","priority":"Medium"},{"description":"Prepare release","priority":"High"}]'

# Delete multiple ToDo items using a names list
frappe-cli bulk delete ToDo --names '["TD-0001","TD-0002"]'
```

---

## 6. Model Context Protocol (MCP) Server Setup

### Stdio Mode (local agents)
Configure your LLM clients (like Claude Desktop or Cursor) to run the CLI directly in stdio mode:

```bash
frappe-cli --profile dev mcp start --transport stdio
```

### Detached Daemon HTTP Mode
Run the server in the background as a daemon to allow HTTP connections:

```bash
# Start background server on port 8765
frappe-cli mcp start --transport http --port 8765 --detach

# Check status (retrieves PID, active profile, log file location)
frappe-cli mcp status

# Shut down the background process group cleanly
frappe-cli mcp stop
```

