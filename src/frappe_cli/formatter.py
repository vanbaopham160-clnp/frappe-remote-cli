import json
from datetime import datetime

from tabulate import tabulate

# ---------------------------------------------------------------------------
# Format helpers (T005)
# ---------------------------------------------------------------------------

def format_date_value(value: str, date_format: str = "plain") -> str:
    """Format a date/datetime string according to the requested regional format.

    Supported formats:
      - 'plain'  → ISO 8601 unchanged  (2024-01-15)
      - 'us'     → MM/DD/YYYY          (01/15/2024)
      - 'french' → DD/MM/YYYY          (15/01/2024)
      - 'german' → DD.MM.YYYY          (15.01.2024)
    """
    if not value or date_format == "plain":
        return str(value) if value is not None else ""

    # Try to parse the value as a date/datetime string
    for fmt_in in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(str(value)[:19], fmt_in)
            if date_format == "us":
                return dt.strftime("%m/%d/%Y")
            elif date_format == "french":
                return dt.strftime("%d/%m/%Y")
            elif date_format == "german":
                return dt.strftime("%d.%m.%Y")
        except ValueError:
            continue

    # Not a parseable date — return as-is
    return str(value)


def format_number_value(value, number_format: str = "plain") -> str:
    """Format a numeric value according to the requested regional format.

    Supported formats:
      - 'plain'  → standard dot decimal, no thousands sep  (1234567.89)
      - 'us'     → comma thousands, dot decimal            (1,234,567.89)
      - 'french' → space thousands, comma decimal          (1 234 567,89)
      - 'german' → dot thousands, comma decimal            (1.234.567,89)
    """
    if value is None or value == "":
        return ""

    try:
        fval = float(value)
    except (ValueError, TypeError):
        return str(value)

    if number_format == "us":
        return f"{fval:,.2f}"
    elif number_format == "french":
        # Use space as thousands separator, comma as decimal
        formatted = f"{fval:,.2f}"
        # swap comma→tilde, dot→comma, tilde→space
        formatted = formatted.replace(",", "~").replace(".", ",").replace("~", "\u00a0")
        return formatted
    elif number_format == "german":
        formatted = f"{fval:,.2f}"
        # swap comma→tilde, dot→comma, tilde→dot
        formatted = formatted.replace(",", "~").replace(".", ",").replace("~", ".")
        return formatted
    else:
        # plain: no thousands separators
        return str(fval)


# Known date-like field names (used for auto-detection when formatting tables)
_DATE_FIELD_HINTS = {
    "creation", "modified", "date", "posting_date", "transaction_date",
    "from_date", "to_date", "start_date", "end_date", "due_date",
}

# Known number-like field types — keys that are *usually* numeric values
_NUMBER_FIELD_HINTS = {
    "amount", "qty", "rate", "total", "net_total", "grand_total",
    "base_amount", "base_total", "base_grand_total", "balance",
    "debit", "credit", "price", "value",
}


def _apply_cell_format(key: str, value, date_format: str, number_format: str) -> str:
    """Decide how to format a single cell value based on field key hint and value type."""
    str_key = str(key).lower()

    # Date fields: detect by field name
    if any(hint in str_key for hint in _DATE_FIELD_HINTS):
        return format_date_value(value, date_format)

    # Numeric fields: format if the value is int/float, or if the key is a known number hint
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if number_format != "plain":
            return format_number_value(value, number_format)
        return str(value)

    if any(hint in str_key for hint in _NUMBER_FIELD_HINTS):
        return format_number_value(value, number_format)

    return str(value) if value is not None else ""


# ---------------------------------------------------------------------------
# Main output formatter (enhanced from T005/T012)
# ---------------------------------------------------------------------------

def format_output(
    data,
    print_json: bool = False,
    date_format: str = "plain",
    number_format: str = "plain",
) -> str:
    """Formats payload as JSON or pretty ASCII table depending on flag.

    Args:
        data: The payload to format (list, dict, or scalar).
        print_json: When True, emit compact JSON.
        date_format: One of 'plain', 'us', 'french', 'german'.
        number_format: One of 'plain', 'us', 'french', 'german'.
    """
    if print_json:
        return json.dumps(data, indent=4, default=str)

    if data is None:
        return "No data returned."

    if isinstance(data, list):
        if not data:
            return "Empty list."

        # If it's a list of dictionaries
        if all(isinstance(x, dict) for x in data):
            # Gather all unique keys across all items for headers
            headers = []
            for item in data:
                for k in item.keys():
                    if k not in headers:
                        headers.append(k)
            rows = []
            for item in data:
                rows.append(
                    [
                        _apply_cell_format(h, item.get(h, ""), date_format, number_format)
                        for h in headers
                    ]
                )
            return tabulate(rows, headers=headers, tablefmt="grid", disable_numparse=True)
        else:
            # Simple list
            rows = [[str(x)] for x in data]
            return tabulate(rows, headers=["Value"], tablefmt="grid", disable_numparse=True)

    if isinstance(data, dict):
        if not data:
            return "Empty object."
        rows = [
            [k, _apply_cell_format(k, v, date_format, number_format)]
            for k, v in data.items()
        ]
        return tabulate(rows, headers=["Key", "Value"], tablefmt="grid")

    return str(data)


def format_bulk_summary(results: list) -> str:
    """Render a summary table for bulk operation results.

    Each item in ``results`` should be a dict with keys:
      - 'name': document identifier
      - 'status': 'ok' | 'error'
      - 'message': detail string
    """
    if not results:
        return "No records processed."

    ok_count = sum(1 for r in results if r.get("status") == "ok")
    err_count = len(results) - ok_count

    rows = [[r.get("name", ""), r.get("status", ""), r.get("message", "")] for r in results]
    table = tabulate(rows, headers=["Name", "Status", "Message"], tablefmt="grid")
    summary = f"\nTotal: {len(results)}  ✓ Success: {ok_count}  ✗ Failed: {err_count}"
    return table + summary


def zip_report_rows(columns: list, data: list) -> list:
    """Convert Frappe run_report response into a list of dicts.

    Frappe returns ``columns`` as a list of dicts (or strings) and ``data``
    as a list of arrays.  This function zips them together into a list of dicts
    keyed by the column fieldname/label.

    Args:
        columns: List of column descriptors (dicts with 'fieldname'/'label', or strings).
        data: List of row arrays.

    Returns:
        List of dicts where each dict maps column label→value.
    """
    labels = []
    for col in columns:
        if isinstance(col, dict):
            labels.append(col.get("fieldname") or col.get("label") or str(col))
        else:
            labels.append(str(col))

    return [dict(zip(labels, row)) for row in data]


def format_schema_fields(fields: list, compact: bool = True) -> list:
    """Filter schema fields to a compact readable set.

    When compact=True, only key attributes are retained per field:
    fieldname, label, fieldtype, options, reqd, read_only.
    """
    if not compact:
        return fields

    keep = {"fieldname", "label", "fieldtype", "options", "reqd", "read_only", "default"}
    return [{k: v for k, v in f.items() if k in keep and v not in (None, "", 0)} for f in fields]
