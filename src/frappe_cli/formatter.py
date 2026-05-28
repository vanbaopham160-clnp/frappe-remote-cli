import json

from tabulate import tabulate


def format_output(data, print_json: bool = False) -> str:
    """Formats payload as JSON or pretty ASCII table depending on flag."""
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
                rows.append([item.get(h, "") for h in headers])
            return tabulate(rows, headers=headers, tablefmt="grid")
        else:
            # Simple list
            rows = [[str(x)] for x in data]
            return tabulate(rows, headers=["Value"], tablefmt="grid")

    if isinstance(data, dict):
        if not data:
            return "Empty object."
        rows = [[k, str(v)] for k, v in data.items()]
        return tabulate(rows, headers=["Key", "Value"], tablefmt="grid")

    return str(data)
