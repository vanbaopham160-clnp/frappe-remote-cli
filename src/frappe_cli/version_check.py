import json
import os
import time
import requests
import click
from frappe_cli import __version__

VERSION_CHECK_CACHE_PATH = os.path.expanduser("~/.config/frappe-cli/version.json")


def parse_version(v):
    """Helper to parse a version string into a comparison-friendly integer tuple."""
    return tuple(int(x) for x in str(v).split(".") if x.isdigit())


def fetch_latest_pypi_version(timeout: float = 3.0) -> str:
    """Fetch the latest version of the package directly from PyPI (bypassing cache)."""
    try:
        res = requests.get("https://pypi.org/pypi/frappe-remote-cli/json", timeout=timeout)
        if res.status_code == 200:
            return res.json().get("info", {}).get("version")
    except Exception:
        pass
    return None


def check_for_updates():
    """Checks PyPI for a newer version of frappe-remote-cli.

    Uses a 24-hour cache file to avoid slowing down commands.
    """
    # Disable version check in testing
    if os.environ.get("FRAPPE_CLI_NO_VERSION_CHECK"):
        return

    now = time.time()
    last_check = 0.0
    latest_version = __version__

    # 1. Read cache
    if os.path.exists(VERSION_CHECK_CACHE_PATH):
        try:
            with open(VERSION_CHECK_CACHE_PATH) as f:
                cache = json.load(f)
                last_check = cache.get("last_check", 0.0)
                latest_version = cache.get("latest_version", __version__)
        except Exception:
            pass

    # 2. Check PyPI if cache is older than 24 hours (86400 seconds)
    if now - last_check > 86400:
        pypi_version = fetch_latest_pypi_version(timeout=1.0)
        if pypi_version:
            latest_version = pypi_version
            try:
                # Write updated cache
                os.makedirs(os.path.dirname(VERSION_CHECK_CACHE_PATH), exist_ok=True)
                with open(VERSION_CHECK_CACHE_PATH, "w") as f:
                    json.dump({"last_check": now, "latest_version": latest_version}, f)
            except Exception:
                pass

    # 3. Compare version numbers
    try:
        if parse_version(latest_version) > parse_version(__version__):
            click.echo(
                click.style(
                    f"\n[notice] A new release of frappe-remote-cli is available: {__version__} -> {latest_version}\n"
                    f"[notice] To update, run: pip install --upgrade frappe-remote-cli",
                    fg="yellow"
                ),
                err=True
            )
    except Exception:
        pass
