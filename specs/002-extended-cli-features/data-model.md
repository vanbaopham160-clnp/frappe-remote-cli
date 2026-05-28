# Data Model: Extended Features and MCP Server

This document defines the schemas and structures utilized by the regional format settings, merged schemas, query reports, and background MCP daemon processes.

---

## 1. Regional Formatting Options

The configuration profile (stored in `~/.frappe-cli.json` or custom `--config` path) is extended with these fields:

```json
{
  "default_profile": "default",
  "profiles": {
    "default": {
      "site_url": "https://mysite.example.com",
      "api_key": "my_api_key",
      "api_secret": "my_api_secret",
      "verify": true,
      "number_format": "french",
      "date_format": "yyyy-mm-dd"
    }
  }
}
```

### Attributes
- **`number_format`** (enum string, optional):
  - `french`: Display format `1 000 000,00` (non-breaking space thousands, comma decimal).
  - `us`: Display format `1,000,000.00` (comma thousands, dot decimal).
  - `german`: Display format `1.000.000,00` (dot thousands, comma decimal).
  - `plain`: Display format `1000000.00` (no grouping, dot decimal).
- **`date_format`** (enum string, optional):
  - `yyyy-mm-dd`: ISO format (e.g. `2026-05-28`).
  - `dd-mm-yyyy`: European dash format (e.g. `28-05-2026`).
  - `dd/mm/yyyy`: European slash format (e.g. `28/05/2026`).
  - `mm/dd/yyyy`: US slash format (e.g. `05/28/2026`).

---

## 2. Merged DocType Schema

The resolved schema returned by the `schema` command merges standard base fields, dynamic custom fields, and option overrides:

```json
{
  "name": "DocType Name",
  "module": "Accounts",
  "is_submittable": 0,
  "issingle": 0,
  "istable": 0,
  "fields": [
    {
      "fieldname": "naming_series",
      "label": "Series",
      "fieldtype": "Select",
      "reqd": 1,
      "options": "INV-2026-.#####\nINV-TEST-.#####"
    },
    {
      "fieldname": "custom_remarks",
      "label": "Remarks",
      "fieldtype": "Text",
      "reqd": 0,
      "custom": 1
    }
  ]
}
```

### Field Merge Logic
1. **Standard Fields**: Extracted directly from `fields` array of base DocType API response.
2. **Custom Fields**: Queried from `Custom Field` doctype.
   - Spliced into the fields array immediately after the field matching its `insert_after` attribute.
   - If `insert_after` does not match any standard fieldname, it is appended to the end of the array.
3. **Dropdown Option Overrides**: Queried from `Property Setter` where `property = "options"`.
   - Patches the `options` attribute of the target standard field in-place.

---

## 3. Query Report Structure

Reports returned by `report <report_name>` are parsed from the `/api/method/frappe.desk.query_report.run` endpoint response:

```json
{
  "columns": [
    {
      "fieldname": "voucher_no",
      "label": "Voucher No",
      "fieldtype": "Link",
      "options": "Journal Entry"
    },
    {
      "fieldname": "debit",
      "label": "Debit",
      "fieldtype": "Currency"
    }
  ],
  "result": [
    ["JV-0001", 1500.00],
    ["JV-0002", 0.00]
  ]
}
```

### Table Representation Mapping
- Columns are extracted from the report's `columns` array.
- Rows from the report's `result` array are parsed:
  - If a row is an array, values are matched index-by-index with columns.
  - If a row is an object, fields are extracted by matching key names.
- Columns are displayed in their original returned index order.

---

## 4. MCP Daemon State Schema

The background MCP server writes its process details to `~/.config/frappe-cli/mcp.json`:

```json
{
  "pid": 12845,
  "port": 8765,
  "started_at": "2026-05-28T10:30:00Z",
  "site": "default",
  "log_path": "/Users/user/.config/frappe-cli/mcp.log"
}
```

### Validation Rules
- **`pid`**: Must correspond to an active running process in the OS (validated via `os.kill(pid, 0)`).
- **`port`**: Must be a valid TCP port number (1-65535).
- **`started_at`**: ISO-8601 UTC timestamp.
