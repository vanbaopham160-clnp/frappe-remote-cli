"""
T020: Unit tests verifying custom field injection indexes and property setter overrides
in the dynamic schema resolver (FrappeClient.get_schema).
"""
import pytest
from unittest.mock import MagicMock, patch, call

from frappe_cli.client import FrappeClient, FrappeException
from frappe_cli.formatter import format_schema_fields


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_client():
    """Create a FrappeClient with dummy credentials (no actual HTTP)."""
    return FrappeClient(
        url="https://example.frappe.cloud",
        api_key="test_key",
        api_secret="test_secret",
        verify=False,
    )


# ---------------------------------------------------------------------------
# get_schema — base fields only
# ---------------------------------------------------------------------------

class TestGetSchemaBaseFields:
    def test_returns_doctype_name_and_fields(self):
        client = make_client()

        base_doc = {
            "name": "Sales Order",
            "fields": [
                {"fieldname": "customer", "label": "Customer", "fieldtype": "Link"},
                {"fieldname": "status", "label": "Status", "fieldtype": "Select"},
            ],
        }

        with patch.object(client, "get_doc", return_value=base_doc), \
             patch.object(client, "get_list", side_effect=FrappeException("no table")):
            schema = client.get_schema("Sales Order")

        assert schema["doctype"] == "Sales Order"
        assert len(schema["fields"]) == 2
        assert schema["fields"][0]["fieldname"] == "customer"

    def test_returns_empty_fields_if_doctype_has_no_fields(self):
        client = make_client()

        with patch.object(client, "get_doc", return_value={"name": "Empty", "fields": []}), \
             patch.object(client, "get_list", side_effect=FrappeException("no table")):
            schema = client.get_schema("Empty")

        assert schema["fields"] == []


# ---------------------------------------------------------------------------
# get_schema — custom field injection
# ---------------------------------------------------------------------------

class TestGetSchemaCustomFields:
    def test_custom_field_appended_when_no_insert_after(self):
        client = make_client()

        base_doc = {
            "fields": [
                {"fieldname": "customer", "fieldtype": "Link"},
            ]
        }
        custom_fields = [
            {
                "name": "Sales Order-custom_ref",
                "fieldname": "custom_ref",
                "label": "Custom Ref",
                "fieldtype": "Data",
                "insert_after": None,
                "idx": 99,
            }
        ]

        def get_list_side(doctype, **kwargs):
            if doctype == "Custom Field":
                return custom_fields
            return []  # Property Setters

        with patch.object(client, "get_doc", return_value=base_doc), \
             patch.object(client, "get_list", side_effect=get_list_side):
            schema = client.get_schema("Sales Order")

        fieldnames = [f["fieldname"] for f in schema["fields"]]
        assert "custom_ref" in fieldnames
        assert schema["fields"][-1]["is_custom_field"] == 1

    def test_custom_field_injected_after_target_field(self):
        client = make_client()

        base_doc = {
            "fields": [
                {"fieldname": "customer", "fieldtype": "Link"},
                {"fieldname": "status", "fieldtype": "Select"},
            ]
        }
        custom_fields = [
            {
                "name": "Sales Order-custom_note",
                "fieldname": "custom_note",
                "label": "Note",
                "fieldtype": "Small Text",
                "insert_after": "customer",
                "idx": 2,
            }
        ]

        def get_list_side(doctype, **kwargs):
            if doctype == "Custom Field":
                return custom_fields
            return []

        with patch.object(client, "get_doc", return_value=base_doc), \
             patch.object(client, "get_list", side_effect=get_list_side):
            schema = client.get_schema("Sales Order")

        fieldnames = [f["fieldname"] for f in schema["fields"]]
        # custom_note should appear after customer (index 1), before status (index 2)
        assert fieldnames.index("custom_note") == fieldnames.index("customer") + 1


# ---------------------------------------------------------------------------
# get_schema — property setter overrides
# ---------------------------------------------------------------------------

class TestGetSchemaPropertySetters:
    def test_options_override_applied(self):
        client = make_client()

        base_doc = {
            "fields": [
                {"fieldname": "status", "fieldtype": "Select", "options": "Draft\nOpen"},
            ]
        }
        setters = [
            {"field_name": "status", "property": "options", "value": "Draft\nOpen\nClosed"}
        ]

        def get_list_side(doctype, **kwargs):
            if doctype == "Custom Field":
                return []
            return setters  # Property Setters

        with patch.object(client, "get_doc", return_value=base_doc), \
             patch.object(client, "get_list", side_effect=get_list_side):
            schema = client.get_schema("Sales Order")

        status_field = next(f for f in schema["fields"] if f["fieldname"] == "status")
        assert status_field["options"] == "Draft\nOpen\nClosed"

    def test_unknown_property_setter_ignored(self):
        """A property setter for a non-existent field should not crash."""
        client = make_client()

        base_doc = {"fields": [{"fieldname": "status", "fieldtype": "Select"}]}
        setters = [
            {"field_name": "nonexistent_field", "property": "options", "value": "X"}
        ]

        def get_list_side(doctype, **kwargs):
            if doctype == "Custom Field":
                return []
            return setters

        with patch.object(client, "get_doc", return_value=base_doc), \
             patch.object(client, "get_list", side_effect=get_list_side):
            # Should not raise
            schema = client.get_schema("Sales Order")

        assert len(schema["fields"]) == 1


# ---------------------------------------------------------------------------
# format_schema_fields (compact filtering)
# ---------------------------------------------------------------------------

class TestFormatSchemaFieldsUnit:
    def test_compact_true_keeps_only_allowed_keys(self):
        fields = [
            {
                "fieldname": "status",
                "label": "Status",
                "fieldtype": "Select",
                "options": "Open\nClosed",
                "reqd": 1,
                "read_only": 0,
                "default": "",
                "in_list_view": 1,
                "search_index": 0,
                "hidden": 0,
                "idx": 3,
            }
        ]
        result = format_schema_fields(fields, compact=True)
        allowed = {"fieldname", "label", "fieldtype", "options", "reqd", "read_only", "default"}
        for key in result[0]:
            assert key in allowed

    def test_compact_removes_falsy_values(self):
        fields = [{"fieldname": "x", "label": "", "fieldtype": "Data", "read_only": 0, "reqd": 0}]
        result = format_schema_fields(fields, compact=True)
        # Empty string, 0 should be filtered out
        assert "label" not in result[0]
        assert "read_only" not in result[0]

    def test_full_false_returns_all_keys(self):
        fields = [{"fieldname": "x", "idx": 1, "hidden": 0, "in_list_view": 1}]
        result = format_schema_fields(fields, compact=False)
        assert result[0]["idx"] == 1
        assert "hidden" in result[0]
