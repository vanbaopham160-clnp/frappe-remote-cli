import base64

import pytest
import responses

from frappe_cli.client import FrappeClient, FrappeException


@responses.activate
def test_client_initialization_and_auth_header():
    client = FrappeClient(
        url="https://testsite.com", api_key="mykey", api_secret="mysecret"
    )

    # Check url normalization
    assert client.url == "https://testsite.com"

    # Check headers dict contains expected Authorization Basic token
    expected_token = base64.b64encode(b"mykey:mysecret").decode("utf-8")
    assert client.headers["Authorization"] == f"Basic {expected_token}"


@responses.activate
def test_check_connection_success():
    client = FrappeClient(
        url="https://testsite.com", api_key="mykey", api_secret="mysecret"
    )

    responses.add(
        responses.GET,
        "https://testsite.com/api/method/frappe.auth.get_logged_user",
        json={"message": "Administrator"},
        status=200,
    )

    user = client.check_connection()
    assert user == "Administrator"


@responses.activate
def test_check_connection_auth_failure():
    client = FrappeClient(
        url="https://testsite.com", api_key="mykey", api_secret="mysecret"
    )

    responses.add(
        responses.GET,
        "https://testsite.com/api/method/frappe.auth.get_logged_user",
        json={"message": "Unauthorized"},
        status=401,
    )

    with pytest.raises(FrappeException) as excinfo:
        client.check_connection()
    assert "Authentication failed" in str(excinfo.value)


@responses.activate
def test_check_connection_server_error_traceback():
    client = FrappeClient(
        url="https://testsite.com", api_key="mykey", api_secret="mysecret"
    )

    responses.add(
        responses.GET,
        "https://testsite.com/api/method/frappe.auth.get_logged_user",
        json={"exc": "Detailed server stacktrace here"},
        status=500,
    )

    with pytest.raises(FrappeException) as excinfo:
        client.check_connection()
    assert "Detailed server stacktrace here" in str(excinfo.value)


@responses.activate
def test_post_api_success():
    client = FrappeClient(
        url="https://testsite.com", api_key="mykey", api_secret="mysecret"
    )

    responses.add(
        responses.POST,
        "https://testsite.com/api/method/my_app.api.add",
        json={"message": 42},
        status=200,
    )

    result = client.post_api("my_app.api.add", params={"a": 10})
    assert result == 42


@responses.activate
def test_get_list_success():
    client = FrappeClient(url="https://testsite.com", api_key="k", api_secret="s")
    responses.add(
        responses.GET,
        "https://testsite.com/api/resource/User",
        json={"data": [{"name": "User 1"}, {"name": "User 2"}]},
        status=200,
    )
    res = client.get_list("User")
    assert len(res) == 2
    assert res[0]["name"] == "User 1"


@responses.activate
def test_get_doc_success():
    client = FrappeClient(url="https://testsite.com", api_key="k", api_secret="s")
    responses.add(
        responses.GET,
        "https://testsite.com/api/resource/User/Administrator",
        json={"data": {"name": "Administrator", "email": "admin@example.com"}},
        status=200,
    )
    res = client.get_doc("User", "Administrator")
    assert res["name"] == "Administrator"
    assert res["email"] == "admin@example.com"


@responses.activate
def test_insert_success():
    client = FrappeClient(url="https://testsite.com", api_key="k", api_secret="s")
    responses.add(
        responses.POST,
        "https://testsite.com/api/resource/User",
        json={"data": {"name": "New User"}},
        status=200,
    )
    res = client.insert("User", {"first_name": "New"})
    assert res["name"] == "New User"


@responses.activate
def test_update_success():
    client = FrappeClient(url="https://testsite.com", api_key="k", api_secret="s")
    responses.add(
        responses.PUT,
        "https://testsite.com/api/resource/User/Administrator",
        json={"data": {"name": "Administrator", "email": "new@example.com"}},
        status=200,
    )
    res = client.update("User", "Administrator", {"email": "new@example.com"})
    assert res["email"] == "new@example.com"


@responses.activate
def test_delete_success():
    client = FrappeClient(url="https://testsite.com", api_key="k", api_secret="s")
    responses.add(
        responses.DELETE,
        "https://testsite.com/api/resource/User/Administrator",
        json={"message": "ok"},
        status=200,
    )
    res = client.delete("User", "Administrator")
    assert res == "ok"
