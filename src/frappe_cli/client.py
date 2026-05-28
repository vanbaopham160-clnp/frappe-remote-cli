import base64
import json

import requests


class FrappeException(Exception):
    """Custom exception raised for remote Frappe API errors."""

    pass


class FrappeClient:
    def __init__(self, url: str, api_key: str, api_secret: str, verify: bool = True):
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret
        self.verify = verify
        self.session = requests.Session()

        self.headers = {
            "Accept": "application/json",
        }
        self._setup_auth()

    def _setup_auth(self):
        """Build and apply the Basic Auth header."""
        auth_str = f"{self.api_key}:{self.api_secret}"
        token = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
        self.headers["Authorization"] = f"Basic {token}"

    def check_connection(self) -> str:
        """Checks the connection by calling frappe.auth.get_logged_user.
        Returns the username of the logged-in user if successful.
        """
        response = self.session.get(
            f"{self.url}/api/method/frappe.auth.get_logged_user",
            headers=self.headers,
            verify=self.verify,
        )
        data = self._post_process(response)
        return data

    def _post_process(self, response: requests.Response):
        """Processes responses, raising exceptions for errors."""
        if response.status_code in (401, 403):
            raise FrappeException(
                f"Authentication failed (HTTP {response.status_code})"
            )
        if response.status_code == 404:
            raise FrappeException("Resource or method not found (HTTP 404)")

        try:
            rjson = response.json()
        except ValueError:
            # Raise exception with raw text for unparseable responses
            raise FrappeException(
                f"Invalid JSON response from server (HTTP {response.status_code}): {response.text}"
            )

        # Check for Frappe-specific exception tracebacks in response body
        if rjson and isinstance(rjson, dict) and rjson.get("exc"):
            raise FrappeException(rjson["exc"])

        if not response.ok:
            raise FrappeException(f"HTTP Error {response.status_code}: {response.text}")

        if isinstance(rjson, dict):
            if "message" in rjson:
                return rjson["message"]
            if "data" in rjson:
                return rjson["data"]
        return rjson

    def post_api(self, method: str, params: dict = None) -> any:
        """Call a remote whitelisted Python method via POST."""
        if params is None:
            params = {}
        # Serialize dicts/lists to JSON strings to match official client preprocessing
        serialized_params = {}
        for k, v in params.items():
            if isinstance(v, (dict, list)):
                serialized_params[k] = json.dumps(v)
            else:
                serialized_params[k] = str(v)

        response = self.session.post(
            f"{self.url}/api/method/{method}",
            data=serialized_params,
            headers=self.headers,
            verify=self.verify,
        )
        return self._post_process(response)

    def get_list(
        self,
        doctype: str,
        fields: list = None,
        filters: list = None,
        limit_start: int = 0,
        limit_page_length: int = None,
        order_by: str = None,
    ) -> list:
        """Get a list of records for a DocType."""
        params = {}
        if fields:
            params["fields"] = json.dumps(fields)
        if filters:
            params["filters"] = json.dumps(filters)
        if limit_page_length is not None:
            params["limit_start"] = limit_start
            params["limit_page_length"] = limit_page_length
        if order_by:
            params["order_by"] = order_by

        response = self.session.get(
            f"{self.url}/api/resource/{doctype}",
            params=params,
            headers=self.headers,
            verify=self.verify,
        )
        return self._post_process(response)

    def get_doc(self, doctype: str, name: str) -> dict:
        """Get details of a specific document by name."""
        response = self.session.get(
            f"{self.url}/api/resource/{doctype}/{name}",
            headers=self.headers,
            verify=self.verify,
        )
        return self._post_process(response)

    def insert(self, doctype: str, doc_data: dict) -> dict:
        """Create a new document."""
        payload = {"data": json.dumps(doc_data)}
        response = self.session.post(
            f"{self.url}/api/resource/{doctype}",
            data=payload,
            headers=self.headers,
            verify=self.verify,
        )
        return self._post_process(response)

    def update(self, doctype: str, name: str, doc_data: dict) -> dict:
        """Update fields of an existing document."""
        payload = {"data": json.dumps(doc_data)}
        response = self.session.put(
            f"{self.url}/api/resource/{doctype}/{name}",
            data=payload,
            headers=self.headers,
            verify=self.verify,
        )
        return self._post_process(response)

    def delete(self, doctype: str, name: str) -> str:
        """Delete a document by name."""
        response = self.session.delete(
            f"{self.url}/api/resource/{doctype}/{name}",
            headers=self.headers,
            verify=self.verify,
        )
        return self._post_process(response)

    # -----------------------------------------------------------------------
    # T014: doc count
    # -----------------------------------------------------------------------

    def count_docs(self, doctype: str, filters: list = None) -> int:
        """Return the total count of documents for a DocType matching filters.

        Uses the Frappe REST API ``/api/resource/<DocType>`` with
        ``limit_page_length=0`` which returns the total count in the response.
        Falls back to ``frappe.client.get_count`` if needed.
        """
        try:
            params = {"limit_page_length": 0}
            if filters:
                params["filters"] = json.dumps(filters)
            response = self.session.get(
                f"{self.url}/api/resource/{doctype}",
                params=params,
                headers=self.headers,
                verify=self.verify,
            )
            result = self._post_process(response)
            # Some Frappe versions return the count in the top-level response
            if isinstance(result, int):
                return result
            # Try method call instead
            raise FrappeException("count_docs: unexpected response format")
        except FrappeException:
            # Fallback: use whitelisted frappe.client.get_count
            params = {"doctype": doctype}
            if filters:
                params["filters"] = json.dumps(filters)
            return self.post_api("frappe.client.get_count", params)

    # -----------------------------------------------------------------------
    # T015: meta listings
    # -----------------------------------------------------------------------

    def list_doctypes(self, filters: list = None) -> list:
        """Return a list of DocType names visible to the current user."""
        return self.get_list(
            "DocType",
            fields=["name", "module", "issingle", "istable"],
            filters=filters,
            limit_page_length=500,
        )

    def list_reports(self, filters: list = None) -> list:
        """Return a list of Report names visible to the current user."""
        return self.get_list(
            "Report",
            fields=["name", "report_type", "ref_doctype", "is_standard"],
            filters=filters,
            limit_page_length=500,
        )

    # -----------------------------------------------------------------------
    # T017: report execution
    # -----------------------------------------------------------------------

    def run_report(self, report_name: str, filters: dict = None) -> dict:
        """Execute a Frappe query or script report and return columns + data.

        Args:
            report_name: The name of the Frappe Report document.
            filters: Optional dict of filter key-value pairs.

        Returns:
            dict with keys 'columns' and 'result' (list of row arrays).
        """
        params = {"report_name": report_name}
        if filters:
            params["filters"] = json.dumps(filters)
        result = self.post_api("frappe.desk.query_report.run", params)
        # Normalise: result may be the full dict or already unwrapped
        if isinstance(result, dict):
            return result
        return {"columns": [], "result": []}

    # -----------------------------------------------------------------------
    # T021: dynamic schema resolver
    # -----------------------------------------------------------------------

    def get_schema(self, doctype: str) -> dict:
        """Perform a three-pass schema resolution for a DocType.

        Pass 1: Fetch the base DocType document (fields list).
        Pass 2: Fetch Custom Fields for this DocType and inject them.
        Pass 3: Apply Property Setter overrides (e.g. options changes).

        Returns a dict with keys:
          - 'doctype': str
          - 'fields': list of merged field dicts
        """
        # Pass 1: base doctype fields
        base = self.get_doc("DocType", doctype)
        fields = list(base.get("fields", []))

        # Pass 2: custom fields
        try:
            custom_fields = self.get_list(
                "Custom Field",
                fields=[
                    "name", "fieldname", "label", "fieldtype", "options",
                    "reqd", "read_only", "default", "insert_after", "idx",
                ],
                filters=[["dt", "=", doctype]],
                limit_page_length=500,
            )
            # Inject custom fields at their specified positions
            for cf in custom_fields:
                insert_after = cf.get("insert_after")
                cf_dict = {k: v for k, v in cf.items() if k not in ("name", "dt")}
                cf_dict["is_custom_field"] = 1
                if insert_after:
                    # Find insertion position
                    pos = next(
                        (i + 1 for i, f in enumerate(fields) if f.get("fieldname") == insert_after),
                        len(fields),
                    )
                    fields.insert(pos, cf_dict)
                else:
                    fields.append(cf_dict)
        except FrappeException:
            pass  # Custom Fields table may not exist on older sites

        # Pass 3: property setter overrides
        try:
            setters = self.get_list(
                "Property Setter",
                fields=["field_name", "property", "value"],
                filters=[["doc_type", "=", doctype]],
                limit_page_length=500,
            )
            for setter in setters:
                fname = setter.get("field_name")
                prop = setter.get("property")
                val = setter.get("value")
                if fname and prop:
                    for field in fields:
                        if field.get("fieldname") == fname:
                            field[prop] = val
                            break
        except FrappeException:
            pass  # Property Setter table may not exist on older sites

        return {"doctype": doctype, "fields": fields}

    # -----------------------------------------------------------------------
    # T025: bulk CRUD helpers
    # -----------------------------------------------------------------------

    def bulk_create(self, doctype: str, records: list) -> list:
        """Create multiple documents sequentially.

        Args:
            doctype: The DocType name.
            records: List of field dicts to create.

        Returns:
            List of result dicts: {'name', 'status', 'message'}.
        """
        results = []
        for rec in records:
            try:
                created = self.insert(doctype, rec)
                name = created.get("name", str(created)) if isinstance(created, dict) else str(created)
                results.append({"name": name, "status": "ok", "message": "Created"})
            except FrappeException as e:
                results.append({"name": rec.get("name", "?"), "status": "error", "message": str(e)})
        return results

    def bulk_update(self, doctype: str, records: list) -> list:
        """Update multiple documents sequentially.

        Args:
            doctype: The DocType name.
            records: List of dicts each containing 'name' and fields to update.

        Returns:
            List of result dicts: {'name', 'status', 'message'}.
        """
        results = []
        for rec in records:
            name = rec.get("name")
            if not name:
                results.append({"name": "?", "status": "error", "message": "Missing 'name' field"})
                continue
            data = {k: v for k, v in rec.items() if k != "name"}
            try:
                self.update(doctype, name, data)
                results.append({"name": name, "status": "ok", "message": "Updated"})
            except FrappeException as e:
                results.append({"name": name, "status": "error", "message": str(e)})
        return results

    def bulk_delete(self, doctype: str, names: list) -> list:
        """Delete multiple documents by name sequentially.

        Args:
            doctype: The DocType name.
            names: List of document names to delete.

        Returns:
            List of result dicts: {'name', 'status', 'message'}.
        """
        results = []
        for name in names:
            try:
                self.delete(doctype, name)
                results.append({"name": name, "status": "ok", "message": "Deleted"})
            except FrappeException as e:
                results.append({"name": name, "status": "error", "message": str(e)})
        return results
