"""
T007: Unit tests for date and number formatters in formatter.py
"""
import pytest

from frappe_cli.formatter import (
    format_date_value,
    format_number_value,
    format_output,
    zip_report_rows,
    format_schema_fields,
    format_bulk_summary,
)


# ---------------------------------------------------------------------------
# format_date_value
# ---------------------------------------------------------------------------

class TestFormatDateValue:
    def test_plain_returns_unchanged(self):
        assert format_date_value("2024-01-15", "plain") == "2024-01-15"

    def test_us_format(self):
        assert format_date_value("2024-01-15", "us") == "01/15/2024"

    def test_french_format(self):
        assert format_date_value("2024-01-15", "french") == "15/01/2024"

    def test_german_format(self):
        assert format_date_value("2024-01-15", "german") == "15.01.2024"

    def test_datetime_string_us(self):
        assert format_date_value("2024-01-15 10:30:00", "us") == "01/15/2024"

    def test_non_date_string_returned_as_is(self):
        assert format_date_value("some-text", "us") == "some-text"

    def test_none_returns_empty(self):
        assert format_date_value(None, "us") == ""

    def test_empty_string_returns_empty(self):
        assert format_date_value("", "us") == ""

    def test_default_is_plain(self):
        assert format_date_value("2024-06-01") == "2024-06-01"


# ---------------------------------------------------------------------------
# format_number_value
# ---------------------------------------------------------------------------

class TestFormatNumberValue:
    def test_plain_no_sep(self):
        result = format_number_value(1234567.89, "plain")
        assert "," not in result
        assert "1234567" in result

    def test_us_comma_thousands(self):
        result = format_number_value(1234567.89, "us")
        assert "1,234,567.89" == result

    def test_french_space_comma_decimal(self):
        result = format_number_value(1234567.89, "french")
        # Should contain comma as decimal separator
        assert "," in result
        # Decimal part should be after comma
        assert result.endswith(",89")

    def test_german_dot_thousands_comma_decimal(self):
        result = format_number_value(1234567.89, "german")
        assert result == "1.234.567,89"

    def test_none_returns_empty(self):
        assert format_number_value(None) == ""

    def test_non_numeric_returned_as_is(self):
        assert format_number_value("hello") == "hello"

    def test_integer_value(self):
        result = format_number_value(1000, "us")
        assert "1,000.00" == result

    def test_default_is_plain(self):
        result = format_number_value(42.5)
        assert "42.5" in result


# ---------------------------------------------------------------------------
# format_output with formatting flags
# ---------------------------------------------------------------------------

class TestFormatOutputWithFormats:
    def test_list_of_dicts_rendered_as_grid(self):
        data = [{"name": "A", "amount": 1000}]
        output = format_output(data, print_json=False, number_format="us")
        assert "A" in output
        # amount field should be formatted
        assert "1,000.00" in output

    def test_json_flag_ignores_formats(self):
        data = [{"name": "A"}]
        output = format_output(data, print_json=True)
        assert '"name"' in output

    def test_empty_list(self):
        assert format_output([]) == "Empty list."

    def test_none_data(self):
        assert format_output(None) == "No data returned."

    def test_dict_renders_as_grid(self):
        data = {"fieldname": "status", "fieldtype": "Select"}
        output = format_output(data)
        assert "fieldname" in output
        assert "status" in output


# ---------------------------------------------------------------------------
# zip_report_rows
# ---------------------------------------------------------------------------

class TestZipReportRows:
    def test_dict_columns(self):
        columns = [{"fieldname": "name"}, {"fieldname": "status"}]
        data = [["DOC-001", "Open"], ["DOC-002", "Closed"]]
        result = zip_report_rows(columns, data)
        assert result[0] == {"name": "DOC-001", "status": "Open"}
        assert result[1] == {"name": "DOC-002", "status": "Closed"}

    def test_string_columns(self):
        columns = ["name", "status"]
        data = [["DOC-001", "Open"]]
        result = zip_report_rows(columns, data)
        assert result[0] == {"name": "DOC-001", "status": "Open"}

    def test_label_fallback(self):
        columns = [{"label": "Document Name"}]
        data = [["DOC-001"]]
        result = zip_report_rows(columns, data)
        assert result[0] == {"Document Name": "DOC-001"}

    def test_empty_data_returns_empty(self):
        assert zip_report_rows([], []) == []


# ---------------------------------------------------------------------------
# format_schema_fields
# ---------------------------------------------------------------------------

class TestFormatSchemaFields:
    def test_compact_keeps_key_attrs(self):
        fields = [
            {"fieldname": "status", "label": "Status", "fieldtype": "Select",
             "options": "Open\nClosed", "in_list_view": 1, "idx": 5}
        ]
        result = format_schema_fields(fields, compact=True)
        assert "fieldname" in result[0]
        assert "in_list_view" not in result[0]
        assert "idx" not in result[0]

    def test_full_preserves_all_keys(self):
        fields = [{"fieldname": "status", "idx": 5, "in_list_view": 1}]
        result = format_schema_fields(fields, compact=False)
        assert result[0]["idx"] == 5
        assert result[0]["in_list_view"] == 1

    def test_compact_removes_empty_values(self):
        fields = [{"fieldname": "x", "label": "", "fieldtype": "Data", "options": None}]
        result = format_schema_fields(fields, compact=True)
        assert "label" not in result[0]
        assert "options" not in result[0]


# ---------------------------------------------------------------------------
# format_bulk_summary
# ---------------------------------------------------------------------------

class TestFormatBulkSummary:
    def test_counts_ok_and_error(self):
        results = [
            {"name": "A", "status": "ok", "message": "Created"},
            {"name": "B", "status": "error", "message": "Permission denied"},
        ]
        output = format_bulk_summary(results)
        assert "✓ Success: 1" in output
        assert "✗ Failed: 1" in output

    def test_empty_results(self):
        assert format_bulk_summary([]) == "No records processed."

    def test_all_ok(self):
        results = [{"name": "A", "status": "ok", "message": "Done"}]
        output = format_bulk_summary(results)
        assert "✓ Success: 1" in output
        assert "✗ Failed: 0" in output
