import json
import os

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.frappe-cli.json")


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
