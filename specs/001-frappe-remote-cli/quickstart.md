# Quickstart Guide: Remote Frappe CLI

This guide will help you install, configure, and use the `frappe-cli` tool to interact with a remote Frappe site.

## Installation

Ensure you have Python 3.10+ installed. Clone this repository and install dependencies:

```bash
pip install -e .
```

This registers the global command `frappe-cli` in your path.

## 1. Configuration Setup

Configure connection details for your remote site. Generate your API Key and API Secret in the User Desk first.

```bash
frappe-cli config set \
  --site-url "https://my-frappe-site.com" \
  --api-key "ab12cd34ef56" \
  --api-secret "gh78ij90kl12"
```

Verify that the connection is successful:

```bash
frappe-cli config check
```

## 2. Remote Method Execution (`call`)

Execute a whitelisted remote method. For example, check the currently logged user:

```bash
frappe-cli call frappe.auth.get_logged_user
```

Calling a method with parameters (e.g., a function `calculate_sum(a, b)`):

```bash
frappe-cli call my_app.api.calculate_sum -p a 10 -p b 20
```

By default, output is raw JSON (perfect for pipeline scripting). To format output as an ASCII table instead:

```bash
frappe-cli call frappe.auth.get_logged_user --table
```

## 3. Document CRUD Operations (`doc`)

### List Documents
```bash
frappe-cli doc list User --fields "name,email,first_name"
```

### Get Specific Document
```bash
frappe-cli doc get User Administrator
```

### Create Document
```bash
frappe-cli doc create CustomDocType -d '{"title": "New Record", "status": "Draft"}'
```

### Update Document
```bash
frappe-cli doc update CustomDocType REC-0001 -d '{"status": "Submitted"}'
```

### Delete Document
```bash
frappe-cli doc delete CustomDocType REC-0001
```
