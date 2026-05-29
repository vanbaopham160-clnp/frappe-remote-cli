import json
import sys

import click
import requests

from frappe_cli.client import FrappeClient, FrappeException
from frappe_cli.config import (
    get_profile_formats,
    load_config,
    remove_profile,
    validate_config,
    validate_date_format,
    validate_number_format,
)


def handle_errors(func):
    """Decorator to catch exceptions and format error messages to stderr."""
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FrappeException as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        except requests.exceptions.ConnectionError:
            click.echo(
                "Error: Failed to connect to the remote server. Check your site URL and network connection.",
                err=True,
            )
            sys.exit(1)
        except requests.exceptions.Timeout:
            click.echo("Error: Request timed out.", err=True)
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            click.echo(f"Network Error: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Unexpected error: {e}", err=True)
            sys.exit(1)

    return wrapper


def get_global_option(name, default=None):
    """Traverses click contexts to find a global option stored in ctx.obj."""
    ctx = click.get_current_context(silent=True)
    while ctx:
        if ctx.obj and name in ctx.obj:
            return ctx.obj[name]
        ctx = ctx.parent
    return default


@click.group()
@click.option("--profile", default=None, help="Use a specific connection profile")
@click.option(
    "--no-verify",
    is_flag=True,
    default=False,
    help="Disable SSL certificate verification",
)
@click.pass_context
def main(ctx, profile, no_verify):
    """Frappe Remote command line interface."""
    ctx.ensure_object(dict)
    ctx.obj["profile"] = profile
    ctx.obj["no_verify"] = no_verify


@main.result_callback()
def process_result(result, **kwargs):
    from frappe_cli.version_check import check_for_updates
    check_for_updates()


# ---------------------------------------------------------------------------
# config group
# ---------------------------------------------------------------------------

@main.group()
def config():
    """Manage connection configuration to remote Frappe site."""
    pass


@config.command(name="set")
@click.option("--site-url", help="URL of the remote Frappe site")
@click.option("--api-key", help="API Key")
@click.option("--api-secret", help="API Secret")
@click.option("--profile", default=None, help="Profile name (defaults to 'default')")
@click.option(
    "--verify/--no-verify", default=True, help="Enable/disable SSL verification"
)
@click.option(
    "--date-format",
    default=None,
    type=click.Choice(["plain", "us", "french", "german"], case_sensitive=False),
    help="Regional date output format",
)
@click.option(
    "--number-format",
    default=None,
    type=click.Choice(["plain", "us", "french", "german"], case_sensitive=False),
    help="Regional number output format",
)
@handle_errors
def config_set(site_url, api_key, api_secret, profile, verify, date_format, number_format):
    """Save connection credentials, URL, and optional regional formats."""
    from frappe_cli.config import save_profile_config
    import sys

    # If no connection details are provided, run the full interactive TUI wizard
    if site_url is None and api_key is None and api_secret is None:
        from frappe_cli.config import is_interactive, prompt_profile_config
        if is_interactive():
            profile, data = prompt_profile_config()
            save_profile_config(profile, data)
            click.echo(f"Configuration saved successfully for profile '{profile}'!")
            return
        else:
            click.echo("Error: Input is not a TTY. Interactive prompts are unavailable. Please provide the required arguments.", err=True)
            sys.exit(1)

    # Prompt for missing ones using InquirerPy if in interactive terminal
    if not site_url or not api_key or not api_secret:
        from frappe_cli.config import is_interactive
        if not is_interactive():
            click.echo("Error: Input is not a TTY. Interactive prompts are unavailable. Please provide the required arguments.", err=True)
            sys.exit(1)

        from InquirerPy import inquirer
        from frappe_cli.config import run_prompt
        try:
            if not site_url:
                site_url = run_prompt(inquirer.text(
                    message="Site URL:",
                    validate=lambda v: len(v.strip()) > 0,
                    invalid_message="Site URL cannot be empty."
                ))
                if site_url is None:
                    raise KeyboardInterrupt()
                site_url = site_url.strip()
                if not site_url.startswith(("http://", "https://")):
                    site_url = "https://" + site_url
            if not api_key:
                api_key = run_prompt(inquirer.text(
                    message="API Key:",
                    validate=lambda v: len(v.strip()) > 0,
                    invalid_message="API Key cannot be empty."
                ))
                if api_key is None:
                    raise KeyboardInterrupt()
                api_key = api_key.strip()
            if not api_secret:
                api_secret = run_prompt(inquirer.secret(
                    message="API Secret:",
                    validate=lambda v: len(v.strip()) > 0,
                    invalid_message="API Secret cannot be empty."
                ))
                if api_secret is None:
                    raise KeyboardInterrupt()
        except KeyboardInterrupt:
            from frappe_cli.config import click_echo_err_exit
            click_echo_err_exit()

    if not profile:
        profile = "default"
    data = {
        "site_url": site_url,
        "api_key": api_key,
        "api_secret": api_secret,
        "verify": verify,
    }
    if date_format:
        data["date_format"] = date_format.lower()
    if number_format:
        data["number_format"] = number_format.lower()

    save_profile_config(profile, data)
    click.echo(f"Configuration saved successfully for profile '{profile}'!")


@config.command(name="show")
@click.option(
    "--format",
    "output_format",
    default="text",
    type=click.Choice(["text", "json", "yaml"], case_sensitive=False),
    help="Output format: text (default), json, or yaml",
)
@handle_errors
def config_show(output_format):
    """Display connection settings (API Secret is masked)."""
    profile = get_global_option("profile")
    config = load_config()
    if not profile:
        profile = config.get("default_profile", "default")

    profiles = config.get("profiles", {})
    if profile not in profiles or not validate_config(config, profile_name=profile):
        if profile == "default":
            click.echo(
                "Error: CLI is not configured. Run 'frappe-cli config set' first.",
                err=True,
            )
        else:
            click.echo(
                f"Error: Profile '{profile}' not found or is not configured.", err=True
            )
        sys.exit(2)

    profile_config = profiles[profile]
    # Mask secret for display
    secret = profile_config.get("api_secret", "")
    masked_config = {**profile_config, "api_secret": "*" * len(secret) if secret else "Not Configured"}

    if output_format == "json":
        click.echo(json.dumps({"profile": profile, **masked_config}, indent=4))
        return

    if output_format == "yaml":
        try:
            import yaml
            click.echo(yaml.dump({"profile": profile, **masked_config}, default_flow_style=False))
        except ImportError:
            # Fallback to manual YAML-like output if PyYAML not installed
            click.echo(f"profile: {profile}")
            for k, v in masked_config.items():
                click.echo(f"{k}: {v}")
        return

    # Default text
    click.echo(f"Profile:       {profile}")
    click.echo(f"Site URL:      {profile_config.get('site_url')}")
    click.echo(f"API Key:       {profile_config.get('api_key')}")
    click.echo(f"API Secret:    {'*' * len(secret) if secret else 'Not Configured'}")
    click.echo(f"Verify SSL:    {profile_config.get('verify', True)}")
    click.echo(f"Date Format:   {profile_config.get('date_format', 'plain')}")
    click.echo(f"Number Format: {profile_config.get('number_format', 'plain')}")


@config.command(name="check")
@handle_errors
def config_check():
    """Verify connectivity with the remote Frappe site."""
    client = get_client()
    user = client.check_connection()
    click.echo("Connection Successful!")
    click.echo(f"Connected as: {user}")


@config.command(name="use")
@click.argument("profile_name", required=False)
@handle_errors
def config_use(profile_name):
    """Set the default configuration profile."""
    from frappe_cli.config import save_config, is_interactive, prompt_profile_selection

    config = load_config()
    profiles = config.get("profiles", {})

    if not profile_name:
        if is_interactive():
            profile_name = prompt_profile_selection(config, "Select profile to use:")
        else:
            click.echo("Error: Input is not a TTY. Interactive prompts are unavailable. Please provide the required arguments.", err=True)
            sys.exit(1)

    if profile_name not in profiles:
        click.echo(f"Error: Profile '{profile_name}' is not configured.", err=True)
        sys.exit(2)
    config["default_profile"] = profile_name
    save_config(config)
    click.echo(f"Default profile set to '{profile_name}'.")


@config.command(name="list")
@handle_errors
def config_list():
    """List all configured connection profiles."""
    config = load_config()
    default_profile = config.get("default_profile", "default")
    profiles = config.get("profiles", {})
    if not profiles:
        click.echo("No profiles configured.")
        return
    for name in sorted(profiles.keys()):
        if name == default_profile:
            click.echo(f"* {name}")
        else:
            click.echo(f"  {name}")


@config.command(name="remove")
@click.argument("profile_name", required=False)
@click.option("-y", "--yes", is_flag=True, default=False, help="Confirm deletion without prompting")
@handle_errors
def config_remove(profile_name, yes):
    """Remove a named connection profile."""
    from frappe_cli.config import is_interactive, prompt_profile_selection, prompt_confirm_deletion

    config = load_config()
    profiles = config.get("profiles", {})

    if not profile_name:
        if is_interactive():
            profile_name = prompt_profile_selection(config, "Select profile to remove:")
        else:
            click.echo("Error: Input is not a TTY. Interactive prompts are unavailable. Please provide the required arguments.", err=True)
            sys.exit(1)



    if not yes and is_interactive():
        if not prompt_confirm_deletion(profile_name):
            click.echo("Operation canceled.")
            return

    removed = remove_profile(profile_name)
    if removed:
        click.echo(f"Profile '{profile_name}' removed successfully.")
    else:
        click.echo(f"Error: Profile '{profile_name}' not found.", err=True)
        sys.exit(2)


# ---------------------------------------------------------------------------
# Helper: resolve client with format settings
# ---------------------------------------------------------------------------

def get_client() -> FrappeClient:
    """Resolves stored configuration and returns an authenticated client.
    Exits with code 2 if CLI configuration is invalid or missing.
    """
    profile = get_global_option("profile")
    cli_no_verify = get_global_option("no_verify", False)
    config = load_config()
    if not profile:
        profile = config.get("default_profile", "default")
    profiles = config.get("profiles", {})
    if profile not in profiles:
        if profile == "default":
            click.echo(
                "Error: CLI is not configured. Run 'frappe-cli config set' first.",
                err=True,
            )
        else:
            click.echo(
                f"Error: Profile '{profile}' not found in configuration.", err=True
            )
        sys.exit(2)
    profile_config = profiles[profile]
    if not validate_config(config, profile_name=profile):
        if profile == "default":
            click.echo(
                "Error: CLI is not configured. Run 'frappe-cli config set' first.",
                err=True,
            )
        else:
            click.echo(
                f"Error: Profile '{profile}' is not configured. Run 'frappe-cli config set --profile {profile}' first.",
                err=True,
            )
        sys.exit(2)
    verify = not cli_no_verify and profile_config.get("verify", True)
    click.echo(f"[Profile: {profile}]", err=True)
    return FrappeClient(
        url=profile_config["site_url"],
        api_key=profile_config["api_key"],
        api_secret=profile_config["api_secret"],
        verify=verify,
    )


def _get_formats() -> tuple:
    """Returns (date_format, number_format) for the active profile."""
    profile = get_global_option("profile")
    config = load_config()
    if not profile:
        profile = config.get("default_profile", "default")
    fmts = get_profile_formats(config, profile)
    return fmts["date_format"], fmts["number_format"]


# ---------------------------------------------------------------------------
# call command
# ---------------------------------------------------------------------------

@main.command(name="call")
@click.argument("dotted_path")
@click.option(
    "-p",
    "--param",
    "params",
    multiple=True,
    type=(str, str),
    help="Parameters as key-value pairs",
)
@click.option(
    "-t",
    "--table",
    "print_table",
    is_flag=True,
    help="Print formatted table instead of JSON",
)
@handle_errors
def cli_call(dotted_path, params, print_table):
    """Execute a remote whitelisted Python method."""
    from frappe_cli.formatter import format_output

    client = get_client()
    params_dict = dict(params)

    # Try parsing integers or floats in params for better usability
    for k, v in params_dict.items():
        if v.isdigit():
            params_dict[k] = int(v)
        else:
            try:
                params_dict[k] = float(v)
            except ValueError:
                pass

    result = client.post_api(dotted_path, params=params_dict)
    date_fmt, num_fmt = _get_formats()
    click.echo(format_output(result, print_json=not print_table, date_format=date_fmt, number_format=num_fmt))


# ---------------------------------------------------------------------------
# doc group
# ---------------------------------------------------------------------------

@main.group(name="doc")
def doc():
    """Perform document CRUD operations on the remote Frappe site."""
    pass


@doc.command(name="list")
@click.argument("doctype")
@click.option("-f", "--fields", help="Comma-separated fields to retrieve")
@click.option(
    "-q", "--filters", help='JSON filters list, e.g. \'[["status", "=", "Open"]]\''
)
@click.option("--limit", type=int, help="Limit number of records returned")
@click.option("--order-by", help="Ordering criteria, e.g. 'creation desc'")
@click.option(
    "-t",
    "--table",
    "print_table",
    is_flag=True,
    help="Print formatted table instead of JSON",
)
@handle_errors
def doc_list(doctype, fields, filters, limit, order_by, print_table):
    """List documents of specified DocType."""
    from frappe_cli.formatter import format_output

    client = get_client()

    fields_list = [f.strip() for f in fields.split(",")] if fields else ["name"]
    filters_parsed = json.loads(filters) if filters else None

    result = client.get_list(
        doctype,
        fields=fields_list,
        filters=filters_parsed,
        limit_page_length=limit,
        order_by=order_by,
    )
    date_fmt, num_fmt = _get_formats()
    click.echo(format_output(result, print_json=not print_table, date_format=date_fmt, number_format=num_fmt))


@doc.command(name="get")
@click.argument("doctype")
@click.argument("name")
@click.option(
    "-t",
    "--table",
    "print_table",
    is_flag=True,
    help="Print formatted table instead of JSON",
)
@handle_errors
def doc_get(doctype, name, print_table):
    """Show details of a specific document."""
    from frappe_cli.formatter import format_output

    client = get_client()
    result = client.get_doc(doctype, name)
    date_fmt, num_fmt = _get_formats()
    click.echo(format_output(result, print_json=not print_table, date_format=date_fmt, number_format=num_fmt))


@doc.command(name="create")
@click.argument("doctype")
@click.option("-d", "--data", required=True, help="JSON data of fields to set")
@click.option(
    "-t",
    "--table",
    "print_table",
    is_flag=True,
    help="Print formatted table instead of JSON",
)
@handle_errors
def doc_create(doctype, data, print_table):
    """Create a new document."""
    from frappe_cli.formatter import format_output

    client = get_client()
    doc_data = json.loads(data)
    result = client.insert(doctype, doc_data)
    date_fmt, num_fmt = _get_formats()
    click.echo(format_output(result, print_json=not print_table, date_format=date_fmt, number_format=num_fmt))


@doc.command(name="update")
@click.argument("doctype")
@click.argument("name")
@click.option("-d", "--data", required=True, help="JSON data of fields to update")
@click.option(
    "-t",
    "--table",
    "print_table",
    is_flag=True,
    help="Print formatted table instead of JSON",
)
@handle_errors
def doc_update(doctype, name, data, print_table):
    """Update fields of an existing document."""
    from frappe_cli.formatter import format_output

    client = get_client()
    doc_data = json.loads(data)
    result = client.update(doctype, name, doc_data)
    date_fmt, num_fmt = _get_formats()
    click.echo(format_output(result, print_json=not print_table, date_format=date_fmt, number_format=num_fmt))


@doc.command(name="delete")
@click.argument("doctype")
@click.argument("name")
@click.option(
    "-t",
    "--table",
    "print_table",
    is_flag=True,
    help="Print formatted table instead of JSON",
)
@handle_errors
def doc_delete(doctype, name, print_table):
    """Delete a document by name."""
    from frappe_cli.formatter import format_output

    client = get_client()
    result = client.delete(doctype, name)
    date_fmt, num_fmt = _get_formats()
    click.echo(format_output(result, print_json=not print_table, date_format=date_fmt, number_format=num_fmt))


@doc.command(name="count")
@click.argument("doctype")
@click.option(
    "-q", "--filters", help='JSON filters list, e.g. \'[["status", "=", "Open"]]\''
)
@handle_errors
def doc_count(doctype, filters):
    """Count documents of a specified DocType."""
    client = get_client()
    filters_parsed = json.loads(filters) if filters else None
    count = client.count_docs(doctype, filters=filters_parsed)
    click.echo(f"Count: {count}")


# ---------------------------------------------------------------------------
# meta group (T015)
# ---------------------------------------------------------------------------

@main.group(name="meta")
def meta():
    """Retrieve metadata from the remote Frappe site."""
    pass


@meta.command(name="doctypes")
@click.option("-q", "--filters", help="JSON filters list to narrow results")
@click.option(
    "-t",
    "--table",
    "print_table",
    is_flag=True,
    help="Print formatted table instead of JSON",
)
@handle_errors
def meta_doctypes(filters, print_table):
    """List all DocTypes visible to the current user."""
    from frappe_cli.formatter import format_output

    client = get_client()
    filters_parsed = json.loads(filters) if filters else None
    result = client.list_doctypes(filters=filters_parsed)
    click.echo(format_output(result, print_json=not print_table))


@meta.command(name="reports")
@click.option("-q", "--filters", help="JSON filters list to narrow results")
@click.option(
    "-t",
    "--table",
    "print_table",
    is_flag=True,
    help="Print formatted table instead of JSON",
)
@handle_errors
def meta_reports(filters, print_table):
    """List all Reports visible to the current user."""
    from frappe_cli.formatter import format_output

    client = get_client()
    filters_parsed = json.loads(filters) if filters else None
    result = client.list_reports(filters=filters_parsed)
    click.echo(format_output(result, print_json=not print_table))


# ---------------------------------------------------------------------------
# report command (T019)
# ---------------------------------------------------------------------------

@main.command(name="report")
@click.argument("report_name")
@click.option(
    "-p",
    "--param",
    "params",
    multiple=True,
    type=(str, str),
    help="Filter key-value pairs, e.g. -p company 'My Company'",
)
@click.option(
    "-t",
    "--table",
    "print_table",
    is_flag=True,
    help="Print formatted table instead of JSON",
)
@handle_errors
def run_report(report_name, params, print_table):
    """Execute a Frappe report by name and display its results."""
    from frappe_cli.formatter import format_output, zip_report_rows

    client = get_client()
    filters_dict = dict(params) if params else {}
    result = client.run_report(report_name, filters=filters_dict if filters_dict else None)

    columns = result.get("columns", [])
    data = result.get("result", result.get("data", []))

    if print_table:
        rows = zip_report_rows(columns, data)
        date_fmt, num_fmt = _get_formats()
        click.echo(format_output(rows, print_json=False, date_format=date_fmt, number_format=num_fmt))
    else:
        click.echo(json.dumps(result, indent=4, default=str))


# ---------------------------------------------------------------------------
# schema command (T023)
# ---------------------------------------------------------------------------

@main.command(name="schema")
@click.argument("doctype")
@click.option(
    "--compact/--full",
    default=True,
    help="Show compact field view (default) or full field details",
)
@click.option(
    "-t",
    "--table",
    "print_table",
    is_flag=True,
    help="Print formatted table instead of JSON",
)
@handle_errors
def get_schema(doctype, compact, print_table):
    """Retrieve the resolved schema (fields) for a DocType."""
    from frappe_cli.formatter import format_output, format_schema_fields

    client = get_client()
    schema = client.get_schema(doctype)
    fields = format_schema_fields(schema.get("fields", []), compact=compact)

    if print_table:
        click.echo(format_output(fields, print_json=False))
    else:
        click.echo(json.dumps({"doctype": doctype, "fields": fields}, indent=4, default=str))


# ---------------------------------------------------------------------------
# bulk group (T027)
# ---------------------------------------------------------------------------

@main.group(name="bulk")
def bulk():
    """Perform bulk create, update, or delete operations."""
    pass


@bulk.command(name="create")
@click.argument("doctype")
@click.option(
    "-d", "--data",
    required=True,
    help="JSON array of field dicts to create, or path to a JSON file prefixed with @",
)
@handle_errors
def bulk_create(doctype, data):
    """Create multiple documents in one call."""
    from frappe_cli.formatter import format_bulk_summary

    records = _load_json_arg(data)
    if not isinstance(records, list):
        click.echo("Error: Data must be a JSON array of objects.", err=True)
        sys.exit(1)

    client = get_client()
    results = client.bulk_create(doctype, records)
    click.echo(format_bulk_summary(results))


@bulk.command(name="update")
@click.argument("doctype")
@click.option(
    "-d", "--data",
    required=True,
    help="JSON array of dicts with 'name' + fields to update, or @file",
)
@handle_errors
def bulk_update(doctype, data):
    """Update multiple documents in one call."""
    from frappe_cli.formatter import format_bulk_summary

    records = _load_json_arg(data)
    if not isinstance(records, list):
        click.echo("Error: Data must be a JSON array of objects.", err=True)
        sys.exit(1)

    client = get_client()
    results = client.bulk_update(doctype, records)
    click.echo(format_bulk_summary(results))


@bulk.command(name="delete")
@click.argument("doctype")
@click.option(
    "-n", "--names",
    required=True,
    help="JSON array of document names to delete, or @file",
)
@handle_errors
def bulk_delete(doctype, names):
    """Delete multiple documents in one call."""
    from frappe_cli.formatter import format_bulk_summary

    name_list = _load_json_arg(names)
    if not isinstance(name_list, list):
        click.echo("Error: Names must be a JSON array of strings.", err=True)
        sys.exit(1)

    client = get_client()
    results = client.bulk_delete(doctype, name_list)
    click.echo(format_bulk_summary(results))


def _load_json_arg(value: str):
    """Load JSON from a literal string or from a @filepath argument."""
    if value.startswith("@"):
        path = value[1:]
        try:
            with open(path) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            click.echo(f"Error reading file '{path}': {e}", err=True)
            sys.exit(1)
    return json.loads(value)


# ---------------------------------------------------------------------------
# mcp group (T034)
# ---------------------------------------------------------------------------

@main.group(name="mcp")
def mcp():
    """Model Context Protocol (MCP) server commands."""
    pass


@mcp.command(name="start")
@click.option(
    "--transport",
    default="stdio",
    type=click.Choice(["stdio", "http"], case_sensitive=False),
    help="Transport mode: stdio (default) or http",
)
@click.option(
    "--port",
    default=8765,
    type=int,
    help="HTTP port for MCP server (only used with --transport=http)",
)
@click.option(
    "--detach",
    is_flag=True,
    default=False,
    help="Run MCP server as a background daemon",
)
@handle_errors
def mcp_start(transport, port, detach):
    """Start the MCP server (stdio or HTTP transport)."""
    from frappe_cli.mcp_server import start_mcp_server

    start_mcp_server(transport=transport, port=port, detach=detach)


@mcp.command(name="status")
@handle_errors
def mcp_status():
    """Check whether the MCP background daemon is running."""
    from frappe_cli.mcp_server import get_daemon_status

    status = get_daemon_status()
    if status.get("running"):
        click.echo(f"MCP daemon is running (PID {status.get('pid')}, port {status.get('port')}).")
    else:
        click.echo("MCP daemon is not running.")


@mcp.command(name="stop")
@handle_errors
def mcp_stop():
    """Stop the MCP background daemon."""
    from frappe_cli.mcp_server import stop_daemon

    stopped = stop_daemon()
    if stopped:
        click.echo("MCP daemon stopped.")
    else:
        click.echo("MCP daemon was not running.")


@main.command(name="update")
@click.option(
    "--check",
    is_flag=True,
    default=False,
    help="Check for updates without installing",
)
@click.option(
    "-y",
    "--yes",
    "assume_yes",
    is_flag=True,
    default=False,
    help="Update without interactive confirmation",
)
@handle_errors
def update_cmd(check, assume_yes):
    """Update frappe-remote-cli to the latest PyPI version."""
    from frappe_cli.version_check import fetch_latest_pypi_version, parse_version
    from frappe_cli import __version__
    import subprocess
    import sys

    click.echo("Checking for updates...")
    latest_version = fetch_latest_pypi_version()
    if not latest_version:
        click.echo("Error: Could not retrieve latest version from PyPI.", err=True)
        sys.exit(1)

    if parse_version(latest_version) <= parse_version(__version__):
        click.echo(f"Your CLI version ({__version__}) is already up to date!")
        return

    click.echo(f"A new version is available: {__version__} -> {latest_version}")
    if check:
        return

    if not assume_yes:
        if not click.confirm("Do you want to update now?", default=True):
            click.echo("Update canceled.")
            return

    click.echo("Upgrading frappe-remote-cli via pip...")
    try:
        # Run pip upgrade using active python interpreter
        res = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "frappe-remote-cli"],
            capture_output=True,
            text=True,
            check=True
        )
        click.echo(res.stdout)
        click.echo(click.style("Upgrade completed successfully!", fg="green"))
    except subprocess.CalledProcessError as e:
        click.echo("Error: Upgrade failed.", err=True)
        click.echo(e.stderr, err=True)
        sys.exit(1)
