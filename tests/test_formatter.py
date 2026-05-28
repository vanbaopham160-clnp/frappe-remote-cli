from frappe_cli.formatter import format_output


def test_format_output_json():
    data = {"hello": "world"}
    res = format_output(data, print_json=True)
    assert '"hello": "world"' in res


def test_format_output_dict_table():
    data = {"name": "Admin", "role": "System Manager"}
    res = format_output(data, print_json=False)
    assert "name" in res
    assert "Admin" in res
    assert "System Manager" in res


def test_format_output_list_dicts_table():
    data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    res = format_output(data, print_json=False)
    assert "Alice" in res
    assert "Bob" in res
    assert "30" in res
    assert "25" in res
