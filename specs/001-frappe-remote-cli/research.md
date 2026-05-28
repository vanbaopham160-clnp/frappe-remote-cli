# Research Notes: Remote Frappe CLI Connection

This document consolidates the technical findings, structural API choices, and libraries chosen for implementing the Remote Frappe CLI.

## Source Code Reference
We inspected the local Frappe client implementation at [frappeclient.py](file:///Users/baor/kegmil/frappe_local/frappe-bench/apps/frappe/frappe/frappeclient.py) to align our client code with the framework's native interface.

## Decisions

### 1. HTTP Client & API Communications
- **Choice**: Python `requests` library.
- **Dotted Path (RPC) Endpoint**: `POST /api/method/<dotted.path.to.method>` or `GET /api/method/<dotted.path.to.method>`.
- **DocType CRUD Endpoints**:
  - **List**: `GET /api/resource/<doctype>`
  - **Get**: `GET /api/resource/<doctype>/<name>`
  - **Create**: `POST /api/resource/<doctype>` (fields passed inside the form body under `data` key, formatted as serialized JSON)
  - **Update**: `PUT /api/resource/<doctype>/<name>` (fields passed inside the form body under `data` key, formatted as serialized JSON)
  - **Delete**: `POST /` with `cmd=frappe.client.delete` (or standard REST DELETE if supported by resource API).

### 2. Authentication Mechanism
- **Choice**: Basic Authentication header using Base64 encoded token.
- **Format**: `Authorization: Basic <base64(api_key:api_secret)>`
- **Rationale**: This matches the exact implementation in the official `FrappeClient` ([frappeclient.py:L89-93](file:///Users/baor/kegmil/frappe_local/frappe-bench/apps/frappe/frappe/frappeclient.py#L89-93)):
  ```python
  token = base64.b64encode((f"{self.api_key}:{self.api_secret}").encode()).decode("utf-8")
  auth_header = { "Authorization": f"Basic {token}" }
  ```

### 3. Local Credentials Storage
- **Choice**: JSON configuration file stored at `~/.frappe-cli.json`
- **Format**:
  ```json
  {
    "site_url": "https://remote.frappe.site",
    "api_key": "your_api_key",
    "api_secret": "your_api_secret"
  }
  ```
- **File Permissions**: Set to `0600` (readable/writable only by owner) to secure the API Secret.

### 4. Output Formatting
- **Choice**: Python `tabulate` library for tables, and `json` module for raw JSON output.
- **Structure**: Default output is a formatted ASCII table. When `--json` is specified, prints raw JSON directly.

---

## Rationale
- **Aligning with Official Client**: By matching `Basic` base64 authentication and `data` serialization parameters, we guarantee maximum compatibility across different versions of the Frappe server.
- **Click Framework**: Click is highly modular, supports nested commands/groups, provides automatic help pages, and supports options/arguments type casting.
- **Requests Library**: Simple, robust, and handles HTTP verbs, JSON serialization/deserialization, headers, and timeouts out-of-the-box.
- **Tabulate**: Creates high-quality formatted ASCII tables with zero configuration, allowing easy terminal visualization.
