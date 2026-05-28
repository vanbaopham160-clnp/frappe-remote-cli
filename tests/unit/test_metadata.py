"""
T008: Unit tests for metadata listings (meta doctypes/reports) and config remove.
"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from frappe_cli.cli import main
from frappe_cli.config import remove_profile


# ---------------------------------------------------------------------------
# config remove command
# ---------------------------------------------------------------------------

class TestConfigRemove:
    def test_remove_existing_profile(self, tmp_path):
        """remove_profile returns True and deletes the profile from config."""
        from frappe_cli.config import save_profile_config, load_config

        config_file = str(tmp_path / "test_config.json")
        save_profile_config(
            "staging",
            {"site_url": "https://staging.example.com", "api_key": "k", "api_secret": "s"},
            path=config_file,
        )
        save_profile_config(
            "default",
            {"site_url": "https://prod.example.com", "api_key": "k", "api_secret": "s"},
            path=config_file,
        )

        result = remove_profile("staging", path=config_file)
        assert result is True

        cfg = load_config(path=config_file)
        assert "staging" not in cfg["profiles"]
        assert "default" in cfg["profiles"]

    def test_remove_nonexistent_profile_returns_false(self, tmp_path):
        config_file = str(tmp_path / "test_config.json")
        result = remove_profile("nonexistent", path=config_file)
        assert result is False

    def test_remove_default_resets_active_profile(self, tmp_path):
        """Removing the active default profile shifts default to the next profile."""
        from frappe_cli.config import save_profile_config, load_config

        config_file = str(tmp_path / "test_config.json")
        save_profile_config(
            "default",
            {"site_url": "https://prod.example.com", "api_key": "k", "api_secret": "s"},
            path=config_file,
        )
        save_profile_config(
            "staging",
            {"site_url": "https://staging.example.com", "api_key": "k", "api_secret": "s"},
            path=config_file,
        )

        remove_profile("default", path=config_file)

        cfg = load_config(path=config_file)
        assert "default" not in cfg["profiles"]
        # default_profile should shift to "staging"
        assert cfg["default_profile"] == "staging"

    def test_cli_config_remove_success(self, tmp_path):
        """CLI 'config remove' command outputs success message."""
        from frappe_cli.config import save_profile_config

        config_file = str(tmp_path / "config.json")
        save_profile_config(
            "staging",
            {"site_url": "https://s.example.com", "api_key": "k", "api_secret": "s"},
            path=config_file,
        )

        runner = CliRunner()
        with patch("frappe_cli.cli.remove_profile") as mock_remove:
            mock_remove.return_value = True
            result = runner.invoke(main, ["config", "remove", "staging"])

        assert result.exit_code == 0
        assert "removed successfully" in result.output

    def test_cli_config_remove_not_found(self):
        """CLI 'config remove' exits with code 2 when profile not found."""
        runner = CliRunner()
        with patch("frappe_cli.cli.remove_profile") as mock_remove:
            mock_remove.return_value = False
            result = runner.invoke(main, ["config", "remove", "ghost"])

        assert result.exit_code == 2


# ---------------------------------------------------------------------------
# meta doctypes command
# ---------------------------------------------------------------------------

class TestMetaDoctypes:
    def _mock_client(self):
        mock = MagicMock()
        mock.list_doctypes.return_value = [
            {"name": "Sales Order", "module": "Selling", "issingle": 0, "istable": 0},
            {"name": "Customer", "module": "Selling", "issingle": 0, "istable": 0},
        ]
        return mock

    def test_meta_doctypes_table_output(self):
        runner = CliRunner()
        with patch("frappe_cli.cli.get_client", return_value=self._mock_client()):
            result = runner.invoke(main, ["meta", "doctypes", "--table"])

        assert result.exit_code == 0
        assert "Sales Order" in result.output
        assert "Customer" in result.output

    def test_meta_doctypes_json_output(self):
        runner = CliRunner()
        with patch("frappe_cli.cli.get_client", return_value=self._mock_client()):
            result = runner.invoke(main, ["meta", "doctypes"])

        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert any(d["name"] == "Sales Order" for d in data)


# ---------------------------------------------------------------------------
# meta reports command
# ---------------------------------------------------------------------------

class TestMetaReports:
    def _mock_client(self):
        mock = MagicMock()
        mock.list_reports.return_value = [
            {"name": "General Ledger", "report_type": "Script Report", "ref_doctype": "GL Entry"},
        ]
        return mock

    def test_meta_reports_table_output(self):
        runner = CliRunner()
        with patch("frappe_cli.cli.get_client", return_value=self._mock_client()):
            result = runner.invoke(main, ["meta", "reports", "--table"])

        assert result.exit_code == 0
        assert "General Ledger" in result.output

    def test_meta_reports_json_output(self):
        runner = CliRunner()
        with patch("frappe_cli.cli.get_client", return_value=self._mock_client()):
            result = runner.invoke(main, ["meta", "reports"])

        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert data[0]["name"] == "General Ledger"


# ---------------------------------------------------------------------------
# doc count command
# ---------------------------------------------------------------------------

class TestDocCount:
    def test_doc_count_no_filters(self):
        mock_client = MagicMock()
        mock_client.count_docs.return_value = 42

        runner = CliRunner()
        with patch("frappe_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(main, ["doc", "count", "Customer"])

        assert result.exit_code == 0
        assert "42" in result.output
        mock_client.count_docs.assert_called_once_with("Customer", filters=None)

    def test_doc_count_with_filters(self):
        mock_client = MagicMock()
        mock_client.count_docs.return_value = 5

        runner = CliRunner()
        with patch("frappe_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(main, ["doc", "count", "Customer", "-q", '[["disabled","=","0"]]'])

        assert result.exit_code == 0
        assert "5" in result.output
