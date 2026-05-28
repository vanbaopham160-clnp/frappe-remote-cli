# CLI Command Contract

This document defines the input and output interface contracts for the `frappe-cli` executable.

## Global Options

The root executable `frappe-cli` accepts global options that modify subcommand behavior.

- **Options**:
  - `--profile TEXT`: Specify the site configuration profile to use (e.g. `frappe-cli --profile staging config check`). Defaults to the value of `default_profile` in the config file.
  - `--no-verify`: Disable SSL certificate verification (e.g. `frappe-cli --no-verify config check`). Overrides any stored profile setting.

## Command Groups and Subcommands

### 1. `frappe-cli config`
Configure connection parameters for the remote site.

- **Usage**: `frappe-cli config set [OPTIONS]`
  - Options:
    - `--site-url TEXT` (Optional. Prompts interactively if omitted)
    - `--api-key TEXT` (Optional. Prompts interactively if omitted)
    - `--api-secret TEXT` (Optional. Prompts interactively if omitted, input is masked)
    - `--profile TEXT` (Optional. Profile name to save to, defaults to `default`)
    - `--verify / --no-verify` (Optional. Enable/disable SSL verification, defaults to verify)
- **Usage**: `frappe-cli config show`
  - Output: Connection URL and API Key (API Secret masked for security). Respects the selected profile.
- **Usage**: `frappe-cli config check`
  - Performs connection diagnostic for the selected profile.
  - Output: "Connection Successful" on stdout, or error traceback/message on stderr.
- **Usage**: `frappe-cli config use <profile_name>`
  - Sets the specified profile as the default profile in the configuration file.
- **Usage**: `frappe-cli config list`
  - Lists all configured profiles, with an asterisk (*) indicating the active default profile.

---

### 2. `frappe-cli call`
Call a remote whitelisted method on the remote Frappe site.

- **Usage**: `frappe-cli call <dotted_path> [OPTIONS]`
  - Arguments:
    - `dotted_path`: Dotted Python path to the remote method (e.g., `frappe.auth.get_logged_user`).
  - Options:
    - `-p, --param KEY VALUE`: Key-value parameters passed to the method (can be specified multiple times).
    - `-t, --table`: Toggle to output formatted ASCII table instead of raw JSON.
- **Stdout Output**: Raw JSON (default) or formatted ASCII table.
- **Stderr Output**: Clean error explanation if the method is not found/whitelisted.

---

### 3. `frappe-cli doc`
Perform document CRUD operations.

- **Subcommands**:
  - `list <doctype>`: List documents of specified DocType.
    - Options:
      - `-f, --fields TEXT`: Comma-separated fields to retrieve (defaults to `name`).
      - `-q, --filters TEXT`: Filter conditions formatted as JSON (e.g. `[["status", "=", "Open"]]`).
  - `get <doctype> <name>`: Show a document's fields and values.
  - `create <doctype>`: Create a new document.
    - Options:
      - `-d, --data TEXT`: JSON string of field values.
  - `update <doctype> <name>`: Update fields of a document.
    - Options:
      - `-d, --data TEXT`: JSON string of fields to update.
  - `delete <doctype> <name>`: Delete a document.

---

## Output Protocols and Exit Codes

### Exit Codes:
- `0`: Success
- `1`: Unhandled error / Network connection issue
- `2`: Invalid command syntax / Missing arguments / Configured profile not found
- `401`: Authentication failure (invalid API Key or Secret)
- `404`: Method or DocType not found on remote site
