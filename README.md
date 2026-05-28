# Frappe Remote CLI Tool

A Python command-line utility built with Click and Requests to communicate with a remote Frappe site (v15).

## Features

- **Local Configuration**: Securely store connection URLs and API credentials locally in `~/.frappe-cli.json` (permissions enforced at `0600`). Supports multiple site profiles.
- **Interactive Prompts**: Prompts you for configuration parameters when setting up connection configs if options are omitted.
- **SSL Verification Control**: Bypass SSL certificate validation using the `--no-verify` option for local or development environments.
- **Remote RPC Executions**: Call any remote whitelisted Python methods on the site via `frappe.call`.
- **REST DocType CRUD**: Query, fetch, insert, update, or delete DocType records using clean subcommand interfaces.
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

### 1. Configuration Setup

```bash
# Set connection parameters (prompts interactively for missing arguments)
frappe-cli config set \
  --site-url "https://my-frappe-site.com" \
  --api-key "ab12cd34ef56" \
  --api-secret "gh78ij90kl12" \
  --profile production

# Interactive config (will prompt for all missing values)
frappe-cli config set --profile staging

# List all configured profiles
frappe-cli config list

# Switch default profile
frappe-cli config use staging

# Inspect active profile configuration
frappe-cli config show

# Run connection diagnostic for active profile
frappe-cli config check

# Run connection diagnostic for a specific profile with SSL validation disabled
frappe-cli --profile staging --no-verify config check
```

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

### 3. Document CRUD (`doc`)

#### List records:
```bash
frappe-cli doc list User --fields "name,email,first_name"
```

#### Get record:
```bash
frappe-cli doc get User Administrator
```

#### Create record:
```bash
frappe-cli doc create User -d '{"email": "new@example.com", "first_name": "New"}'
```

#### Update record:
```bash
frappe-cli doc update User new@example.com -d '{"first_name": "UpdatedName"}'
```

#### Delete record:
```bash
frappe-cli doc delete User new@example.com
```

---

## Running Tests

Run the test suite containing unit, integration, and formatting tests:

```bash
pytest
```
