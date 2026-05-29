import json
import os

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.frappe-cli.json")

# Valid format enumerations
VALID_DATE_FORMATS = {"us", "french", "german", "plain"}
VALID_NUMBER_FORMATS = {"us", "french", "german", "plain"}


def get_config_path() -> str:
    """Returns the default configuration file path."""
    return DEFAULT_CONFIG_PATH


def normalize_config(config_data: dict) -> dict:
    """Normalizes configuration to the multi-profile format."""
    if not isinstance(config_data, dict):
        return {"default_profile": "default", "profiles": {}}

    # Already in new multi-profile format
    if "profiles" in config_data:
        # Ensure default_profile exists
        if "default_profile" not in config_data:
            config_data["default_profile"] = "default"
        return config_data

    # Legacy format conversion
    if (
        "site_url" in config_data
        or "api_key" in config_data
        or "api_secret" in config_data
    ):
        profile_data = {}
        for key in ["site_url", "api_key", "api_secret", "verify"]:
            if key in config_data:
                profile_data[key] = config_data[key]
        return {"default_profile": "default", "profiles": {"default": profile_data}}

    return {"default_profile": "default", "profiles": {}}


def load_config(path: str = None) -> dict:
    """Loads configuration dictionary from path, normalized to multi-profile format."""
    if path is None:
        path = DEFAULT_CONFIG_PATH
    if not os.path.exists(path):
        return {"default_profile": "default", "profiles": {}}
    try:
        with open(path) as f:
            data = json.load(f)
            return normalize_config(data)
    except (json.JSONDecodeError, OSError):
        return {"default_profile": "default", "profiles": {}}


def save_config(config_data: dict, path: str = None) -> None:
    """Saves configuration dictionary to path and updates file permissions to 0600."""
    if path is None:
        path = DEFAULT_CONFIG_PATH
    # Ensure parent directory exists
    parent_dir = os.path.dirname(path)

    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    with open(path, "w") as f:
        json.dump(config_data, f, indent=4)

    try:
        os.chmod(path, 0o600)
    except OSError:
        pass  # In some environments (e.g. Windows/testing) chmod might fail or behave differently


def save_profile_config(
    profile_name: str, profile_data: dict, path: str = None
) -> None:
    """Saves/updates a specific profile configuration, keeping other profiles intact."""
    current_config = load_config(path)
    normalized = normalize_config(current_config)

    if "profiles" not in normalized:
        normalized["profiles"] = {}

    normalized["profiles"][profile_name] = profile_data

    # If default_profile is not set, or is 'default' but we set another profile first, let's make it the default
    if not normalized.get("default_profile") or (
        normalized.get("default_profile") == "default"
        and "default" not in normalized["profiles"]
    ):
        normalized["default_profile"] = profile_name

    # If default_profile was set to some profile that doesn't exist anymore, reset it
    if normalized.get("default_profile") not in normalized["profiles"]:
        normalized["default_profile"] = profile_name

    save_config(normalized, path)


def remove_profile(profile_name: str, path: str = None) -> bool:
    """Removes a named profile from the configuration.

    Returns True if the profile was found and removed, False if not found.
    If the removed profile was the default, resets default_profile to the first
    remaining profile or 'default' if none remain.
    """
    config = load_config(path)
    profiles = config.get("profiles", {})

    if profile_name not in profiles:
        return False

    del profiles[profile_name]
    config["profiles"] = profiles

    # Reset default if we removed the active default
    if config.get("default_profile") == profile_name:
        remaining = list(profiles.keys())
        config["default_profile"] = remaining[0] if remaining else "default"

    save_config(config, path)
    return True


def validate_config(config_data: dict, profile_name: str = None) -> bool:
    """Validates configuration parameters for a profile."""
    if not isinstance(config_data, dict):
        return False

    # If the input is already a normalized config dictionary
    if "profiles" in config_data:
        if not profile_name:
            profile_name = config_data.get("default_profile", "default")
        profiles = config_data.get("profiles", {})
        profile_data = profiles.get(profile_name)
    else:
        # Otherwise, check if it's a direct legacy config dict
        profile_data = config_data

    if not isinstance(profile_data, dict):
        return False

    site_url = profile_data.get("site_url")
    api_key = profile_data.get("api_key")
    api_secret = profile_data.get("api_secret")

    if not site_url or not isinstance(site_url, str):
        return False
    if not site_url.startswith(("http://", "https://")):
        return False
    if not api_key or not isinstance(api_key, str):
        return False
    if not api_secret or not isinstance(api_secret, str):
        return False

    return True


def validate_date_format(fmt: str) -> bool:
    """Returns True if fmt is a recognized date format label."""
    return fmt in VALID_DATE_FORMATS


def validate_number_format(fmt: str) -> bool:
    """Returns True if fmt is a recognized number format label."""
    return fmt in VALID_NUMBER_FORMATS


def get_profile_formats(config: dict, profile_name: str = None) -> dict:
    """Returns the date_format and number_format settings for a profile.

    Falls back to 'plain' for each unset setting.
    """
    if not profile_name:
        profile_name = config.get("default_profile", "default")
    profiles = config.get("profiles", {})
    profile = profiles.get(profile_name, {})
    return {
        "date_format": profile.get("date_format", "plain"),
        "number_format": profile.get("number_format", "plain"),
    }


def is_interactive() -> bool:
    """Returns True if the current process standard input and output is an interactive terminal."""
    import sys
    return sys.stdin.isatty() and sys.stdout.isatty()


def run_prompt(prompt_obj):
    """Executes a prompt object and registers escape key to exit (returning None)."""
    @prompt_obj.register_kb("escape")
    def _(event):
        event.app.exit(result=None)
    return prompt_obj.execute()


def prompt_profile_config():
    """Run an interactive wizard using InquirerPy to collect profile settings.

    Returns:
        tuple: (profile_name, data_dict)
    """
    from InquirerPy import inquirer
    import sys

    try:
        url = run_prompt(inquirer.text(
            message="Site URL:",
            validate=lambda val: len(val.strip()) > 0,
            invalid_message="Site URL cannot be empty."
        ))
        if url is None:
            raise KeyboardInterrupt()
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        api_key = run_prompt(inquirer.text(
            message="API Key:",
            validate=lambda val: len(val.strip()) > 0,
            invalid_message="API Key cannot be empty."
        ))
        if api_key is None:
            raise KeyboardInterrupt()

        api_secret = run_prompt(inquirer.secret(
            message="API Secret:",
            validate=lambda val: len(val.strip()) > 0,
            invalid_message="API Secret cannot be empty."
        ))
        if api_secret is None:
            raise KeyboardInterrupt()

        date_format = run_prompt(inquirer.select(
            message="Date Format:",
            choices=["plain", "us", "french", "german"],
            default="plain",
        ))
        if date_format is None:
            raise KeyboardInterrupt()

        number_format = run_prompt(inquirer.select(
            message="Number Format:",
            choices=["plain", "us", "french", "german"],
            default="plain",
        ))
        if number_format is None:
            raise KeyboardInterrupt()

        profile_name = run_prompt(inquirer.text(
            message="Profile Name:",
            default="default",
            validate=lambda val: len(val.strip()) > 0,
            invalid_message="Profile Name cannot be empty."
        ))
        if profile_name is None:
            raise KeyboardInterrupt()
        profile_name = profile_name.strip() or "default"

        return profile_name, {
            "site_url": url,
            "api_key": api_key.strip(),
            "api_secret": api_secret,
            "verify": True,
            "date_format": date_format,
            "number_format": number_format,
        }
    except KeyboardInterrupt:
        click_echo_err_exit()


def click_echo_err_exit():
    import click
    import sys
    click.echo("Operation canceled.", err=True)
    sys.exit(1)


def prompt_profile_selection(config_data: dict, message: str = "Select a profile:") -> str:
    """Prompt the user to select one of the configured profiles.

    Returns:
        str: Selected profile name.
    """
    from InquirerPy import inquirer
    import sys

    profiles = list(config_data.get("profiles", {}).keys())
    if not profiles:
        import click
        click.echo("Error: No profiles configured. Run 'frappe-cli config set' first.", err=True)
        sys.exit(2)

    try:
        selection = run_prompt(inquirer.select(
            message=message,
            choices=profiles,
        ))
        if selection is None:
            raise KeyboardInterrupt()
        return selection
    except KeyboardInterrupt:
        click_echo_err_exit()


def prompt_confirm_deletion(profile_name: str) -> bool:
    """Prompt the user to confirm deletion of a profile."""
    from InquirerPy import inquirer
    try:
        confirm = run_prompt(inquirer.confirm(
            message=f"Are you sure you want to remove profile '{profile_name}'?",
            default=False,
        ))
        if confirm is None:
            raise KeyboardInterrupt()
        return confirm
    except KeyboardInterrupt:
        click_echo_err_exit()
