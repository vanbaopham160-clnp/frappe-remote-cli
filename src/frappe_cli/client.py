import base64

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
        import json

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
        import json

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
        import json

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
        import json

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
