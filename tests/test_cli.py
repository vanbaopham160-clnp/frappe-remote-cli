import os
from unittest.mock import patch

import pytest
import responses
from click.testing import CliRunner

import frappe_cli.config as config_module
from frappe_cli.cli import main


@pytest.fixture
def mock_config_path(tmp_path):
    """Fixture to redirect configuration to a temporary file."""
    config_file = tmp_path / ".frappe-cli.json"
    with patch.object(config_module, "DEFAULT_CONFIG_PATH", str(config_file)):
        yield config_file


def test_config_set_and_show(mock_config_path):
    runner = CliRunner()

    # 1. Initially show should error out as config file is missing/invalid
    result = runner.invoke(main, ["config", "show"])
    assert result.exit_code == 2
    assert "CLI is not configured" in result.output

    # 2. Perform config set
    result = runner.invoke(
        main,
        [
            "config",
            "set",
            "--site-url",
            "https://mysite.frappe.cloud",
            "--api-key",
            "my-api-key",
            "--api-secret",
            "my-api-secret",
        ],
    )
    assert result.exit_code == 0
    assert "Configuration saved successfully" in result.output

    # Verify the file was written
    assert os.path.exists(mock_config_path)

    # 3. Perform config show and verify output
    result = runner.invoke(main, ["config", "show"])
    assert result.exit_code == 0
    assert "https://mysite.frappe.cloud" in result.output
    assert "my-api-key" in result.output
    assert "my-api-secret" not in result.output  # Secret must be masked!
    assert "********" in result.output


@responses.activate
def test_config_check_success(mock_config_path):
    runner = CliRunner()

    # Set config first
    runner.invoke(
        main,
        [
            "config",
            "set",
            "--site-url",
            "https://mysite.frappe.cloud",
            "--api-key",
            "my-api-key",
            "--api-secret",
            "my-api-secret",
        ],
    )

    # Mock remote API check_connection endpoint
    responses.add(
        responses.GET,
        "https://mysite.frappe.cloud/api/method/frappe.auth.get_logged_user",
        json={"message": "Administrator"},
        status=200,
    )

    result = runner.invoke(main, ["config", "check"])
    assert result.exit_code == 0
    assert "Connection Successful!" in result.output
    assert "Connected as: Administrator" in result.output


@responses.activate
def test_config_check_failure(mock_config_path):
    runner = CliRunner()

    # Set config first
    runner.invoke(
        main,
        [
            "config",
            "set",
            "--site-url",
            "https://mysite.frappe.cloud",
            "--api-key",
            "my-api-key",
            "--api-secret",
            "my-api-secret",
        ],
    )

    # Mock remote API failing with 401 Unauthorized
    responses.add(
        responses.GET,
        "https://mysite.frappe.cloud/api/method/frappe.auth.get_logged_user",
        status=401,
    )

    result = runner.invoke(main, ["config", "check"])
    assert result.exit_code == 1
    assert "Error: Authentication failed" in result.output


@responses.activate
def test_cli_call_success(mock_config_path):
    runner = CliRunner()

    # Set config first
    runner.invoke(
        main,
        [
            "config",
            "set",
            "--site-url",
            "https://mysite.frappe.cloud",
            "--api-key",
            "my-api-key",
            "--api-secret",
            "my-api-secret",
        ],
    )

    # Mock method endpoint
    responses.add(
        responses.POST,
        "https://mysite.frappe.cloud/api/method/my_app.api.add",
        json={"message": 42},
        status=200,
    )

    result = runner.invoke(main, ["call", "my_app.api.add", "-p", "a", "10"])
    assert result.exit_code == 0
    assert "42" in result.output


@responses.activate
def test_cli_doc_list(mock_config_path):
    runner = CliRunner()
    runner.invoke(
        main,
        [
            "config",
            "set",
            "--site-url",
            "https://mysite.frappe.cloud",
            "--api-key",
            "k",
            "--api-secret",
            "s",
        ],
    )
    responses.add(
        responses.GET,
        "https://mysite.frappe.cloud/api/resource/User",
        json={"data": [{"name": "User 1", "email": "u1@example.com"}]},
        status=200,
    )
    result = runner.invoke(main, ["doc", "list", "User", "--fields", "name,email"])
    assert result.exit_code == 0
    assert "User 1" in result.output
    assert "u1@example.com" in result.output


@responses.activate
def test_cli_doc_list_params(mock_config_path):
    runner = CliRunner()
    runner.invoke(
        main,
        [
            "config",
            "set",
            "--site-url",
            "https://mysite.frappe.cloud",
            "--api-key",
            "k",
            "--api-secret",
            "s",
        ],
    )
    responses.add(
        responses.GET,
        "https://mysite.frappe.cloud/api/resource/User",
        json={"data": [{"name": "User 1"}]},
        status=200,
    )
    result = runner.invoke(
        main, ["doc", "list", "User", "--limit", "5", "--order-by", "creation desc"]
    )
    assert result.exit_code == 0
    assert "User 1" in result.output


@responses.activate
def test_cli_doc_get(mock_config_path):
    runner = CliRunner()
    runner.invoke(
        main,
        [
            "config",
            "set",
            "--site-url",
            "https://mysite.frappe.cloud",
            "--api-key",
            "k",
            "--api-secret",
            "s",
        ],
    )
    responses.add(
        responses.GET,
        "https://mysite.frappe.cloud/api/resource/User/Administrator",
        json={"data": {"name": "Administrator", "email": "admin@example.com"}},
        status=200,
    )
    result = runner.invoke(main, ["doc", "get", "User", "Administrator"])
    assert result.exit_code == 0
    assert "Administrator" in result.output
    assert "admin@example.com" in result.output


@responses.activate
def test_cli_doc_create(mock_config_path):
    runner = CliRunner()
    runner.invoke(
        main,
        [
            "config",
            "set",
            "--site-url",
            "https://mysite.frappe.cloud",
            "--api-key",
            "k",
            "--api-secret",
            "s",
        ],
    )
    responses.add(
        responses.POST,
        "https://mysite.frappe.cloud/api/resource/User",
        json={"data": {"name": "New User"}},
        status=200,
    )
    result = runner.invoke(
        main, ["doc", "create", "User", "-d", '{"first_name": "New"}']
    )
    assert result.exit_code == 0
    assert "New User" in result.output


@responses.activate
def test_cli_doc_update(mock_config_path):
    runner = CliRunner()
    runner.invoke(
        main,
        [
            "config",
            "set",
            "--site-url",
            "https://mysite.frappe.cloud",
            "--api-key",
            "k",
            "--api-secret",
            "s",
        ],
    )
    responses.add(
        responses.PUT,
        "https://mysite.frappe.cloud/api/resource/User/Administrator",
        json={"data": {"email": "new@example.com"}},
        status=200,
    )
    result = runner.invoke(
        main,
        [
            "doc",
            "update",
            "User",
            "Administrator",
            "-d",
            '{"email": "new@example.com"}',
        ],
    )
    assert result.exit_code == 0
    assert "new@example.com" in result.output


@responses.activate
def test_cli_doc_delete(mock_config_path):
    runner = CliRunner()
    runner.invoke(
        main,
        [
            "config",
            "set",
            "--site-url",
            "https://mysite.frappe.cloud",
            "--api-key",
            "k",
            "--api-secret",
            "s",
        ],
    )
    responses.add(
        responses.DELETE,
        "https://mysite.frappe.cloud/api/resource/User/Administrator",
        json={"message": "ok"},
        status=200,
    )
    result = runner.invoke(main, ["doc", "delete", "User", "Administrator"])
    assert result.exit_code == 0
    assert "ok" in result.output


@responses.activate
def test_cli_doc_list_table(mock_config_path):
    runner = CliRunner()
    runner.invoke(
        main,
        [
            "config",
            "set",
            "--site-url",
            "https://mysite.frappe.cloud",
            "--api-key",
            "k",
            "--api-secret",
            "s",
        ],
    )
    responses.add(
        responses.GET,
        "https://mysite.frappe.cloud/api/resource/User",
        json={"data": [{"name": "User 1", "email": "u1@example.com"}]},
        status=200,
    )
    result = runner.invoke(
        main, ["doc", "list", "User", "--fields", "name,email", "--table"]
    )
    assert result.exit_code == 0
    assert "+" in result.output
    assert "|" in result.output


def test_config_set_interactive(mock_config_path):
    runner = CliRunner()
    # Invoke without options, providing input interactively
    result = runner.invoke(
        main,
        ["config", "set"],
        input="https://interactive.site\nmy-interactive-key\nmy-interactive-secret\n",
    )
    assert result.exit_code == 0
    assert "Configuration saved successfully" in result.output

    # Verify it saved under default profile
    result = runner.invoke(main, ["config", "show"])
    assert "https://interactive.site" in result.output
    assert "my-interactive-key" in result.output


def test_multi_profile_workflow(mock_config_path):
    runner = CliRunner()

    # 1. Create a "prod" profile
    result = runner.invoke(
        main,
        [
            "config",
            "set",
            "--profile",
            "prod",
            "--site-url",
            "https://prod.frappe.site",
            "--api-key",
            "prodkey",
            "--api-secret",
            "prodsecret",
            "--no-verify",
        ],
    )
    assert result.exit_code == 0

    # 2. Create a "dev" profile
    result = runner.invoke(
        main,
        [
            "config",
            "set",
            "--profile",
            "dev",
            "--site-url",
            "https://dev.frappe.site",
            "--api-key",
            "devkey",
            "--api-secret",
            "devsecret",
        ],
    )
    assert result.exit_code == 0

    # 3. List profiles. Default profile is currently prod because it was created first
    result = runner.invoke(main, ["config", "list"])
    assert result.exit_code == 0
    assert "* prod" in result.output
    assert "dev" in result.output

    # 4. Use "dev" profile as default
    result = runner.invoke(main, ["config", "use", "dev"])
    assert result.exit_code == 0
    assert "Default profile set to 'dev'" in result.output

    # 5. List profiles again to verify "dev" is default
    result = runner.invoke(main, ["config", "list"])
    assert "* dev" in result.output

    # 6. Show "prod" using global flag
    result = runner.invoke(main, ["--profile", "prod", "config", "show"])
    assert result.exit_code == 0
    assert "https://prod.frappe.site" in result.output

    # 7. Check show for non-existent profile
    result = runner.invoke(main, ["--profile", "nonexistent", "config", "show"])
    assert result.exit_code == 2
    assert "Profile 'nonexistent' not found" in result.output


@responses.activate
def test_no_verify_parameter(mock_config_path):
    runner = CliRunner()

    # Set up config with verify default
    runner.invoke(
        main,
        [
            "config",
            "set",
            "--site-url",
            "https://mysite.frappe.cloud",
            "--api-key",
            "my-api-key",
            "--api-secret",
            "my-api-secret",
        ],
    )

    responses.add(
        responses.GET,
        "https://mysite.frappe.cloud/api/method/frappe.auth.get_logged_user",
        json={"message": "Administrator"},
        status=200,
    )

    with patch("frappe_cli.cli.FrappeClient") as mock_client:
        # Since wraps=FrappeClient was failing due to missing import, let's just mock it
        # Or import FrappeClient to wrap it properly
        from frappe_cli.client import FrappeClient

        mock_client.side_effect = FrappeClient
        result = runner.invoke(main, ["--no-verify", "config", "check"])
        assert result.exit_code == 0
        mock_client.assert_called_once()
        assert mock_client.call_args[1].get("verify") is False
