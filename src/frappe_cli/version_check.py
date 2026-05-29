import json
import os
import time
import requests
import click
from frappe_cli import __version__

VERSION_CHECK_CACHE_PATH = os.path.expanduser("~/.config/frappe-cli/version.json")


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
        try:
            # Short timeout to avoid blocking CLI
            res = requests.get("https://pypi.org/pypi/frappe-remote-cli/json", timeout=1.0)
            if res.status_code == 200:
                pypi_version = res.json().get("info", {}).get("version")
                if pypi_version:
                    latest_version = pypi_version
                    # Write updated cache
                    os.makedirs(os.path.dirname(VERSION_CHECK_CACHE_PATH), exist_ok=True)
                    with open(VERSION_CHECK_CACHE_PATH, "w") as f:
                        json.dump({"last_check": now, "latest_version": latest_version}, f)
        except Exception:
            # Suppress network errors/timeouts to avoid interrupting CLI usage
            pass

    # 3. Compare version numbers (simple semver check)
    try:
        def parse_version(v):
            return tuple(int(x) for x in str(v).split(".") if x.isdigit())

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
