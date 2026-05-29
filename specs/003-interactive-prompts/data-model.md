# Data Model: Interactive Setup Prompts

This document outlines the data model and input validation rules for the interactive setup wizard configuration parameters.

---

## 1. Setup Input Entity

Represents the data structure collected during the `config set` wizard prompt.

| Field Name | Data Type | Validation Rules | Default Value | Prompt Style |
| :--- | :--- | :--- | :--- | :--- |
| `site_url` | String | Must be a valid URL. If scheme (http/https) is missing, auto-prepend `https://`. | *Required* | Text Input |
| `api_key` | String | Must be a non-empty alphanumeric string. | *Required* | Text Input |
| `api_secret` | String | Must be a non-empty string. Masked on screen. | *Required* | Hidden Password |
| `date_format` | Enum | Choice of: `plain`, `us`, `french`, `german` | `plain` | List Selector |
| `number_format`| Enum | Choice of: `plain`, `us`, `french`, `german` | `plain` | List Selector |
| `profile_name` | String | Must be alphanumeric or use simple dashes/underscores. | `default` | Text Input |

---

## 2. Selection Choice Entity

Represents the data structure used for picking an active profile (`config use`) or removing a profile (`config remove`).

- **Choices**: Extracted dynamically from the list of keys under `profiles` in `~/.frappe-cli.json`.
- **Pre-check**: If no profiles exist, the selector is not displayed; the command exits immediately.
