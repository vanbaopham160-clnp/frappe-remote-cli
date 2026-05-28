"""
T016: Unit tests for report array-zipping and table printing.
"""
import json
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from frappe_cli.formatter import zip_report_rows, format_output
from frappe_cli.cli import main


# ---------------------------------------------------------------------------
# zip_report_rows (core utility)
# ---------------------------------------------------------------------------

class TestZipReportRowsCoverage:
    """Additional edge-case tests for report row zipping."""

    def test_dict_columns_with_fieldname(self):
        columns = [{"fieldname": "party"}, {"fieldname": "debit"}, {"fieldname": "credit"}]
        data = [["Customer A", 5000.0, 0.0], ["Customer B", 0.0, 2000.0]]
        result = zip_report_rows(columns, data)
        assert len(result) == 2
        assert result[0]["party"] == "Customer A"
        assert result[0]["debit"] == 5000.0
        assert result[1]["credit"] == 2000.0

    def test_label_only_columns(self):
        """If column has no fieldname, use label."""
        columns = [{"label": "Party"}, {"label": "Amount"}]
        data = [["Vendor A", 100]]
        result = zip_report_rows(columns, data)
        assert result[0]["Party"] == "Vendor A"
        assert result[0]["Amount"] == 100

    def test_partial_row_shorter_than_columns(self):
        """Rows shorter than columns list are zipped to the shorter length."""
        columns = [{"fieldname": "a"}, {"fieldname": "b"}, {"fieldname": "c"}]
        data = [["x", "y"]]  # Only 2 values but 3 columns
        result = zip_report_rows(columns, data)
        # zip stops at shortest
        assert "c" not in result[0]
        assert result[0]["a"] == "x"

    def test_empty_columns_and_data(self):
        assert zip_report_rows([], []) == []

    def test_mixed_string_and_dict_columns(self):
        columns = ["name", {"fieldname": "amount"}]
        data = [["DOC-001", 999.99]]
        result = zip_report_rows(columns, data)
        assert result[0]["name"] == "DOC-001"
        assert result[0]["amount"] == 999.99


# ---------------------------------------------------------------------------
# Report printing via format_output
# ---------------------------------------------------------------------------

class TestReportTablePrinting:
    def test_report_rows_render_as_table(self):
        """zip_report_rows output should format correctly as a grid table."""
        columns = [{"fieldname": "name"}, {"fieldname": "grand_total"}]
        data = [["SO-001", 15000.0], ["SO-002", 8500.5]]
        rows = zip_report_rows(columns, data)

        output = format_output(rows, print_json=False, number_format="us")
        assert "SO-001" in output
        assert "SO-002" in output
        # grand_total is a number field hint — should be formatted
        assert "15,000.00" in output

    def test_report_json_output(self):
        columns = [{"fieldname": "name"}]
        data = [["SO-001"]]
        rows = zip_report_rows(columns, data)

        output = format_output(rows, print_json=True)
        parsed = json.loads(output)
        assert parsed[0]["name"] == "SO-001"


# ---------------------------------------------------------------------------
# CLI report command integration (mocked)
# ---------------------------------------------------------------------------

class TestReportCLICommand:
    def _mock_client(self):
        mock = MagicMock()
        mock.run_report.return_value = {
            "columns": [{"fieldname": "name"}, {"fieldname": "grand_total"}],
            "result": [["SO-001", 15000], ["SO-002", 8500]],
        }
        return mock

    def test_report_table_output(self):
        runner = CliRunner()
        with patch("frappe_cli.cli.get_client", return_value=self._mock_client()):
            result = runner.invoke(main, ["report", "Sales Order Summary", "--table"])

        assert result.exit_code == 0
        assert "SO-001" in result.output

    def test_report_json_output(self):
        runner = CliRunner()
        with patch("frappe_cli.cli.get_client", return_value=self._mock_client()):
            result = runner.invoke(main, ["report", "Sales Order Summary"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "columns" in parsed or "result" in parsed

    def test_report_with_filters(self):
        mock = self._mock_client()
        runner = CliRunner()
        with patch("frappe_cli.cli.get_client", return_value=mock):
            result = runner.invoke(main, [
                "report", "Sales Order Summary", "-p", "company", "My Company"
            ])

        assert result.exit_code == 0
        mock.run_report.assert_called_once_with(
            "Sales Order Summary", filters={"company": "My Company"}
        )
