import os
import tempfile

from frappe_cli.config import load_config, save_config, validate_config


def test_load_config_nonexistent():
    # Loading config from a file that does not exist should return normalized empty profiles
    assert load_config("/path/to/nowhere/nonexistent.json") == {
        "default_profile": "default",
        "profiles": {},
    }


def test_save_and_load_config():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        data = {
            "site_url": "https://test.frappe.site",
            "api_key": "testkey",
            "api_secret": "testsecret",
        }
        save_config(data, tmp_path)

        # Verify it loads and normalizes legacy formats correctly
        loaded = load_config(tmp_path)
        assert loaded["default_profile"] == "default"
        assert loaded["profiles"]["default"] == data

        # Check permissions on Unix-like environments (0600)
        if os.name != "nt":
            mode = os.stat(tmp_path).st_mode & 0o777
            assert mode == 0o600
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_validate_config():
    # Valid configurations
    assert (
        validate_config(
            {
                "site_url": "https://test.frappe.site",
                "api_key": "testkey",
                "api_secret": "testsecret",
            }
        )
        is True
    )

    assert (
        validate_config(
            {"site_url": "http://localhost:8000", "api_key": "abc", "api_secret": "def"}
        )
        is True
    )

    # Invalid configurations
    assert validate_config({}) is False
    assert validate_config("not a dict") is False

    # Missing parameters
    assert (
        validate_config({"site_url": "https://test.frappe.site", "api_key": "testkey"})
        is False
    )

    # Invalid url schemes
    assert (
        validate_config(
            {
                "site_url": "ftp://test.frappe.site",
                "api_key": "testkey",
                "api_secret": "testsecret",
            }
        )
        is False
    )


def test_normalize_config_legacy():
    # Legacy config structure should be migrated to multi-profile
    legacy = {
        "site_url": "https://legacy.frappe.site",
        "api_key": "legacykey",
        "api_secret": "legacysecret",
        "verify": False,
    }
    from frappe_cli.config import normalize_config

    normalized = normalize_config(legacy)
    assert normalized["default_profile"] == "default"
    assert normalized["profiles"]["default"]["site_url"] == "https://legacy.frappe.site"
    assert normalized["profiles"]["default"]["api_key"] == "legacykey"
    assert normalized["profiles"]["default"]["api_secret"] == "legacysecret"
    assert normalized["profiles"]["default"]["verify"] is False


def test_normalize_config_empty_or_invalid():
    from frappe_cli.config import normalize_config

    assert normalize_config({}) == {"default_profile": "default", "profiles": {}}
    assert normalize_config("invalid") == {"default_profile": "default", "profiles": {}}


def test_save_profile_config():
    from frappe_cli.config import load_config, save_profile_config

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        profile_a = {
            "site_url": "https://sitea.com",
            "api_key": "keya",
            "api_secret": "secreta",
        }
        profile_b = {
            "site_url": "https://siteb.com",
            "api_key": "keyb",
            "api_secret": "secretb",
            "verify": False,
        }

        # Save first profile
        save_profile_config("sitea", profile_a, tmp_path)
        loaded = load_config(tmp_path)
        assert loaded["default_profile"] == "sitea"
        assert loaded["profiles"]["sitea"]["site_url"] == "https://sitea.com"

        # Save second profile
        save_profile_config("siteb", profile_b, tmp_path)
        loaded = load_config(tmp_path)
        # default_profile should still be sitea
        assert loaded["default_profile"] == "sitea"
        assert loaded["profiles"]["sitea"]["site_url"] == "https://sitea.com"
        assert loaded["profiles"]["siteb"]["site_url"] == "https://siteb.com"
        assert loaded["profiles"]["siteb"]["verify"] is False
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
