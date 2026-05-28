"""
T024: Unit tests for bulk CRUD loop successes and exception catching.
"""
import pytest
from unittest.mock import patch, MagicMock, call
from click.testing import CliRunner

from frappe_cli.client import FrappeClient, FrappeException
from frappe_cli.cli import main
from frappe_cli.formatter import format_bulk_summary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_client():
    return FrappeClient(
        url="https://example.frappe.cloud",
        api_key="key",
        api_secret="secret",
        verify=False,
    )


# ---------------------------------------------------------------------------
# bulk_create
# ---------------------------------------------------------------------------

class TestBulkCreate:
    def test_all_success(self):
        client = make_client()
        records = [
            {"customer_name": "Alice", "customer_type": "Individual"},
            {"customer_name": "Bob", "customer_type": "Company"},
        ]
        with patch.object(client, "insert", side_effect=[
            {"name": "CUST-0001"},
            {"name": "CUST-0002"},
        ]):
            results = client.bulk_create("Customer", records)

        assert len(results) == 2
        assert results[0]["status"] == "ok"
        assert results[0]["name"] == "CUST-0001"
        assert results[1]["status"] == "ok"

    def test_partial_failure(self):
        client = make_client()
        records = [
            {"customer_name": "Alice"},
            {"customer_name": "Bad Record"},
        ]
        with patch.object(client, "insert", side_effect=[
            {"name": "CUST-0001"},
            FrappeException("Validation Error"),
        ]):
            results = client.bulk_create("Customer", records)

        assert results[0]["status"] == "ok"
        assert results[1]["status"] == "error"
        assert "Validation Error" in results[1]["message"]

    def test_all_failure(self):
        client = make_client()
        records = [{"customer_name": "X"}]
        with patch.object(client, "insert", side_effect=FrappeException("Permission denied")):
            results = client.bulk_create("Customer", records)

        assert results[0]["status"] == "error"

    def test_empty_records(self):
        client = make_client()
        results = client.bulk_create("Customer", [])
        assert results == []


# ---------------------------------------------------------------------------
# bulk_update
# ---------------------------------------------------------------------------

class TestBulkUpdate:
    def test_all_success(self):
        client = make_client()
        records = [
            {"name": "CUST-0001", "phone": "123"},
            {"name": "CUST-0002", "phone": "456"},
        ]
        with patch.object(client, "update", return_value={}):
            results = client.bulk_update("Customer", records)

        assert all(r["status"] == "ok" for r in results)
        assert results[0]["name"] == "CUST-0001"

    def test_missing_name_field(self):
        client = make_client()
        records = [{"phone": "123"}]  # No 'name' key
        results = client.bulk_update("Customer", records)

        assert results[0]["status"] == "error"
        assert "Missing 'name'" in results[0]["message"]

    def test_partial_failure_continues(self):
        client = make_client()
        records = [
            {"name": "CUST-0001", "phone": "123"},
            {"name": "CUST-0002", "phone": "bad"},
        ]
        with patch.object(client, "update", side_effect=[
            {},
            FrappeException("Update failed"),
        ]):
            results = client.bulk_update("Customer", records)

        assert results[0]["status"] == "ok"
        assert results[1]["status"] == "error"


# ---------------------------------------------------------------------------
# bulk_delete
# ---------------------------------------------------------------------------

class TestBulkDelete:
    def test_all_success(self):
        client = make_client()
        names = ["CUST-0001", "CUST-0002", "CUST-0003"]
        with patch.object(client, "delete", return_value="ok"):
            results = client.bulk_delete("Customer", names)

        assert len(results) == 3
        assert all(r["status"] == "ok" for r in results)

    def test_partial_failure(self):
        client = make_client()
        names = ["CUST-0001", "CUST-NOT-FOUND"]
        with patch.object(client, "delete", side_effect=[
            "ok",
            FrappeException("Not found"),
        ]):
            results = client.bulk_delete("Customer", names)

        assert results[0]["status"] == "ok"
        assert results[1]["status"] == "error"
        assert "Not found" in results[1]["message"]

    def test_empty_names(self):
        client = make_client()
        results = client.bulk_delete("Customer", [])
        assert results == []


# ---------------------------------------------------------------------------
# CLI bulk commands (integration via Click test runner)
# ---------------------------------------------------------------------------

class TestBulkCLICommands:
    def test_bulk_create_cli(self):
        mock_client = MagicMock()
        mock_client.bulk_create.return_value = [
            {"name": "CUST-0001", "status": "ok", "message": "Created"},
        ]
        runner = CliRunner()
        with patch("frappe_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(main, [
                "bulk", "create", "Customer",
                "-d", '[{"customer_name": "Alice"}]',
            ])

        assert result.exit_code == 0
        assert "CUST-0001" in result.output

    def test_bulk_update_cli(self):
        mock_client = MagicMock()
        mock_client.bulk_update.return_value = [
            {"name": "CUST-0001", "status": "ok", "message": "Updated"},
        ]
        runner = CliRunner()
        with patch("frappe_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(main, [
                "bulk", "update", "Customer",
                "-d", '[{"name": "CUST-0001", "phone": "123"}]',
            ])

        assert result.exit_code == 0
        assert "CUST-0001" in result.output

    def test_bulk_delete_cli(self):
        mock_client = MagicMock()
        mock_client.bulk_delete.return_value = [
            {"name": "CUST-0001", "status": "ok", "message": "Deleted"},
        ]
        runner = CliRunner()
        with patch("frappe_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(main, [
                "bulk", "delete", "Customer",
                "-n", '["CUST-0001"]',
            ])

        assert result.exit_code == 0
        assert "CUST-0001" in result.output

    def test_bulk_create_invalid_json(self):
        mock_client = MagicMock()
        runner = CliRunner()
        with patch("frappe_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(main, [
                "bulk", "create", "Customer",
                "-d", "not json",
            ])

        assert result.exit_code != 0

    def test_bulk_create_non_array_json(self):
        mock_client = MagicMock()
        runner = CliRunner()
        with patch("frappe_cli.cli.get_client", return_value=mock_client):
            result = runner.invoke(main, [
                "bulk", "create", "Customer",
                "-d", '{"key": "value"}',  # Object, not array
            ])

        assert result.exit_code == 1
