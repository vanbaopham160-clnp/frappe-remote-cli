import sys

import click
import requests

from frappe_cli.client import FrappeClient, FrappeException
from frappe_cli.config import load_config, validate_config


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


@main.group()
def config():
    """Manage connection configuration to remote Frappe site."""
    pass


@config.command(name="set")
@click.option("--site-url", prompt="Site URL", help="URL of the remote Frappe site")
@click.option("--api-key", prompt="API Key", help="API Key")
@click.option("--api-secret", prompt="API Secret", hide_input=True, help="API Secret")
@click.option("--profile", default=None, help="Profile name (defaults to 'default')")
@click.option(
    "--verify/--no-verify", default=True, help="Enable/disable SSL verification"
)
@handle_errors
def config_set(site_url, api_key, api_secret, profile, verify):
    """Save connection credentials and URL."""
    from frappe_cli.config import save_profile_config

    if not profile:
        profile = "default"
    data = {
        "site_url": site_url,
        "api_key": api_key,
        "api_secret": api_secret,
        "verify": verify,
    }
    save_profile_config(profile, data)
    click.echo(f"Configuration saved successfully for profile '{profile}'!")


@config.command(name="show")
@handle_errors
def config_show():
    """Display connection settings (API Secret is masked)."""
    profile = get_global_option("profile")
    from frappe_cli.config import load_config

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
    click.echo(f"Profile:  {profile}")
    click.echo(f"Site URL: {profile_config.get('site_url')}")
    click.echo(f"API Key:  {profile_config.get('api_key')}")
    secret = profile_config.get("api_secret", "")
    masked_secret = "*" * len(secret) if secret else "Not Configured"
    click.echo(f"API Secret: {masked_secret}")
    verify = profile_config.get("verify", True)
    click.echo(f"Verify SSL: {verify}")


@config.command(name="check")
@handle_errors
def config_check():
    """Verify connectivity with the remote Frappe site."""
    client = get_client()
    user = client.check_connection()
    click.echo("Connection Successful!")
    click.echo(f"Connected as: {user}")


@config.command(name="use")
@click.argument("profile_name")
@handle_errors
def config_use(profile_name):
    """Set the default configuration profile."""
    from frappe_cli.config import load_config, save_config

    config = load_config()
    profiles = config.get("profiles", {})
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
    from frappe_cli.config import load_config

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
    return FrappeClient(
        url=profile_config["site_url"],
        api_key=profile_config["api_key"],
        api_secret=profile_config["api_secret"],
        verify=verify,
    )


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
    click.echo(format_output(result, print_json=not print_table))


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
    import json

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
    click.echo(format_output(result, print_json=not print_table))


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
    click.echo(format_output(result, print_json=not print_table))


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
    import json

    from frappe_cli.formatter import format_output

    client = get_client()
    doc_data = json.loads(data)
    result = client.insert(doctype, doc_data)
    click.echo(format_output(result, print_json=not print_table))


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
    import json

    from frappe_cli.formatter import format_output

    client = get_client()
    doc_data = json.loads(data)
    result = client.update(doctype, name, doc_data)
    click.echo(format_output(result, print_json=not print_table))


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
    click.echo(format_output(result, print_json=not print_table))
