import json
import os
import time
from unittest.mock import MagicMock, patch
import pytest

from frappe_cli import __version__
from frappe_cli.version_check import check_for_updates


@pytest.fixture
def clean_cache_path(tmp_path):
    """Sets a temporary path for the version cache file."""
    temp_cache = tmp_path / "version.json"
    with patch("frappe_cli.version_check.VERSION_CHECK_CACHE_PATH", str(temp_cache)):
        yield temp_cache


@patch.dict(os.environ, {}, clear=True)
def test_no_pypi_call_if_cache_fresh(clean_cache_path):
    # Setup cache: checked 10 seconds ago, latest version is the same
    clean_cache_path.write_text(
        json.dumps({"last_check": time.time() - 10, "latest_version": __version__})
    )

    with patch("requests.get") as mock_get, patch("click.echo") as mock_echo:
        check_for_updates()
        mock_get.assert_not_called()
        mock_echo.assert_not_called()


@patch.dict(os.environ, {}, clear=True)
def test_pypi_call_if_cache_expired(clean_cache_path):
    # Cache expired 2 days ago
    clean_cache_path.write_text(
        json.dumps({"last_check": time.time() - 172800, "latest_version": __version__})
    )

    # Mock PyPI returning a newer version
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"info": {"version": "99.9.9"}}

    with patch("requests.get", return_value=mock_res) as mock_get, patch("click.echo") as mock_echo:
        check_for_updates()
        mock_get.assert_called_once_with(
            "https://pypi.org/pypi/frappe-remote-cli/json", timeout=1.0
        )
        assert mock_echo.call_count == 1
        # Check cache file is updated
        with open(clean_cache_path) as f:
            cache = json.load(f)
            assert cache["latest_version"] == "99.9.9"
            assert cache["last_check"] > time.time() - 5


@patch.dict(os.environ, {}, clear=True)
def test_pypi_call_fails_gracefully(clean_cache_path):
    # Expired cache
    clean_cache_path.write_text(
        json.dumps({"last_check": time.time() - 172800, "latest_version": __version__})
    )

    # PyPI request raises connection error
    with patch("requests.get", side_effect=Exception("Connection refused")), patch("click.echo") as mock_echo:
        # Should complete without throwing exception
        check_for_updates()
        mock_echo.assert_not_called()


@patch.dict(os.environ, {}, clear=True)
def test_no_print_if_same_version(clean_cache_path):
    # Expired cache
    clean_cache_path.write_text(
        json.dumps({"last_check": time.time() - 172800, "latest_version": __version__})
    )

    # PyPI returns same version
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"info": {"version": __version__}}

    with patch("requests.get", return_value=mock_res), patch("click.echo") as mock_echo:
        check_for_updates()
        mock_echo.assert_not_called()


def test_update_already_up_to_date():
    from frappe_cli.cli import main
    from click.testing import CliRunner

    runner = CliRunner()
    with patch("frappe_cli.version_check.fetch_latest_pypi_version", return_value=__version__):
        res = runner.invoke(main, ["update"])
        assert res.exit_code == 0
        assert "already up to date" in res.output


def test_update_check_only():
    from frappe_cli.cli import main
    from click.testing import CliRunner

    runner = CliRunner()
    with patch("frappe_cli.version_check.fetch_latest_pypi_version", return_value="99.9.9"):
        res = runner.invoke(main, ["update", "--check"])
        assert res.exit_code == 0
        assert "A new version is available" in res.output
        assert "Upgrading" not in res.output


def test_update_upgrade_yes():
    from frappe_cli.cli import main
    from click.testing import CliRunner
    import subprocess

    runner = CliRunner()
    mock_run = MagicMock()
    mock_run.stdout = "Upgraded package successfully"
    
    with patch("frappe_cli.version_check.fetch_latest_pypi_version", return_value="99.9.9"), \
         patch("subprocess.run", return_value=mock_run) as mock_sub:
        res = runner.invoke(main, ["update", "--yes"])
        assert res.exit_code == 0
        assert "Upgraded package successfully" in res.output
        assert "Upgrade completed successfully!" in res.output
        mock_sub.assert_called_once()
