"""
MCP Server for frappe-cli.

Exposes frappe-cli operations as native MCP tools over stdio or HTTP transport.
Supports running as a background daemon with state tracked in a JSON state file.

Tasks covered: T029 (tool mappings), T030 (stdio), T031 (HTTP), T032 (daemon), T033 (state).
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys

# MCP state file location
_MCP_STATE_DIR = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
    "frappe-cli",
)
_MCP_STATE_FILE = os.path.join(_MCP_STATE_DIR, "mcp.json")


# ---------------------------------------------------------------------------
# Daemon state helpers (T033)
# ---------------------------------------------------------------------------

def _load_state() -> dict:
    """Load the MCP daemon state from the JSON state file."""
    if not os.path.exists(_MCP_STATE_FILE):
        return {}
    try:
        with open(_MCP_STATE_FILE) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(state: dict) -> None:
    """Persist MCP daemon state to the JSON state file."""
    os.makedirs(_MCP_STATE_DIR, exist_ok=True)
    with open(_MCP_STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)
    try:
        os.chmod(_MCP_STATE_FILE, 0o600)
    except OSError:
        pass


def _clear_state() -> None:
    """Remove the MCP daemon state file."""
    if os.path.exists(_MCP_STATE_FILE):
        try:
            os.remove(_MCP_STATE_FILE)
        except OSError:
            pass


def get_daemon_status() -> dict:
    """Return {'running': bool, 'pid': int|None, 'port': int|None}."""
    state = _load_state()
    pid = state.get("pid")
    if pid is None:
        return {"running": False, "pid": None, "port": None}

    # Check if the process is actually alive
    try:
        os.kill(pid, 0)
        return {"running": True, "pid": pid, "port": state.get("port")}
    except (ProcessLookupError, PermissionError):
        _clear_state()
        return {"running": False, "pid": None, "port": None}


def stop_daemon() -> bool:
    """Stop the background MCP daemon.

    Returns True if a daemon was found and stopped, False otherwise.
    """
    state = _load_state()
    pid = state.get("pid")
    if pid is None:
        return False

    try:
        os.kill(pid, signal.SIGTERM)
        _clear_state()
        return True
    except (ProcessLookupError, PermissionError):
        _clear_state()
        return False


# ---------------------------------------------------------------------------
# MCP server builder (T029, T030, T031)
# ---------------------------------------------------------------------------

def _build_mcp_server():
    """Build and return a configured MCP Server instance with all tool mappings."""
    try:
        import mcp.types as types
        from mcp.server import Server
        from mcp.server.models import InitializationOptions
        from mcp.types import TextContent, Tool
    except ImportError as exc:
        raise ImportError(
            "The 'mcp' package is required for MCP server support. "
            "Install it with: pip install mcp"
        ) from exc

    from frappe_cli.client import FrappeClient, FrappeException
    from frappe_cli.config import get_profile_formats, load_config
    from frappe_cli.formatter import (
        format_bulk_summary,
        format_output,
        format_schema_fields,
        zip_report_rows,
    )

    server = Server("frappe-cli")

    def _get_client():
        """Build a FrappeClient from the active profile."""
        config = load_config()
        profile_name = config.get("default_profile", "default")
        profiles = config.get("profiles", {})
        profile = profiles.get(profile_name, {})
        if not profile.get("site_url"):
            raise RuntimeError("frappe-cli is not configured. Run 'frappe-cli config set'.")
        return FrappeClient(
            url=profile["site_url"],
            api_key=profile.get("api_key", ""),
            api_secret=profile.get("api_secret", ""),
            verify=profile.get("verify", True),
        )

    def _get_formats():
        config = load_config()
        profile_name = config.get("default_profile", "default")
        fmts = get_profile_formats(config, profile_name)
        return fmts["date_format"], fmts["number_format"]

    # ---- Tool definitions ----

    @server.list_tools()
    async def list_tools():
        return [
            Tool(name="doc_list", description="List documents of a DocType",
                 inputSchema={"type": "object", "properties": {
                     "doctype": {"type": "string"}, "fields": {"type": "string"},
                     "filters": {"type": "string"}, "limit": {"type": "integer"},
                     "order_by": {"type": "string"}}, "required": ["doctype"]}),
            Tool(name="doc_get", description="Get a specific document",
                 inputSchema={"type": "object", "properties": {
                     "doctype": {"type": "string"}, "name": {"type": "string"}},
                     "required": ["doctype", "name"]}),
            Tool(name="doc_create", description="Create a new document",
                 inputSchema={"type": "object", "properties": {
                     "doctype": {"type": "string"}, "data": {"type": "object"}},
                     "required": ["doctype", "data"]}),
            Tool(name="doc_update", description="Update an existing document",
                 inputSchema={"type": "object", "properties": {
                     "doctype": {"type": "string"}, "name": {"type": "string"},
                     "data": {"type": "object"}}, "required": ["doctype", "name", "data"]}),
            Tool(name="doc_delete", description="Delete a document",
                 inputSchema={"type": "object", "properties": {
                     "doctype": {"type": "string"}, "name": {"type": "string"}},
                     "required": ["doctype", "name"]}),
            Tool(name="doc_count", description="Count documents of a DocType",
                 inputSchema={"type": "object", "properties": {
                     "doctype": {"type": "string"}, "filters": {"type": "string"}},
                     "required": ["doctype"]}),
            Tool(name="call", description="Call a whitelisted Frappe method",
                 inputSchema={"type": "object", "properties": {
                     "method": {"type": "string"}, "params": {"type": "object"}},
                     "required": ["method"]}),
            Tool(name="meta_doctypes", description="List all DocTypes",
                 inputSchema={"type": "object", "properties": {
                     "filters": {"type": "string"}}}),
            Tool(name="meta_reports", description="List all Reports",
                 inputSchema={"type": "object", "properties": {
                     "filters": {"type": "string"}}}),
            Tool(name="run_report", description="Execute a Frappe report",
                 inputSchema={"type": "object", "properties": {
                     "report_name": {"type": "string"}, "filters": {"type": "object"}},
                     "required": ["report_name"]}),
            Tool(name="get_schema", description="Get the merged schema of a DocType",
                 inputSchema={"type": "object", "properties": {
                     "doctype": {"type": "string"}, "compact": {"type": "boolean"}},
                     "required": ["doctype"]}),
            Tool(name="bulk_create", description="Bulk create documents",
                 inputSchema={"type": "object", "properties": {
                     "doctype": {"type": "string"}, "records": {"type": "array"}},
                     "required": ["doctype", "records"]}),
            Tool(name="bulk_update", description="Bulk update documents",
                 inputSchema={"type": "object", "properties": {
                     "doctype": {"type": "string"}, "records": {"type": "array"}},
                     "required": ["doctype", "records"]}),
            Tool(name="bulk_delete", description="Bulk delete documents",
                 inputSchema={"type": "object", "properties": {
                     "doctype": {"type": "string"}, "names": {"type": "array"}},
                     "required": ["doctype", "names"]}),
            Tool(name="check_connection", description="Verify connection to the Frappe site",
                 inputSchema={"type": "object", "properties": {}}),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        try:
            client = _get_client()
            date_fmt, num_fmt = _get_formats()

            if name == "doc_list":
                fields = [f.strip() for f in arguments["fields"].split(",")] if arguments.get("fields") else ["name"]
                filters = json.loads(arguments["filters"]) if arguments.get("filters") else None
                result = client.get_list(
                    arguments["doctype"],
                    fields=fields,
                    filters=filters,
                    limit_page_length=arguments.get("limit"),
                    order_by=arguments.get("order_by"),
                )
                return [TextContent(type="text", text=format_output(result, date_format=date_fmt, number_format=num_fmt))]

            elif name == "doc_get":
                result = client.get_doc(arguments["doctype"], arguments["name"])
                return [TextContent(type="text", text=format_output(result, date_format=date_fmt, number_format=num_fmt))]

            elif name == "doc_create":
                result = client.insert(arguments["doctype"], arguments["data"])
                return [TextContent(type="text", text=format_output(result))]

            elif name == "doc_update":
                result = client.update(arguments["doctype"], arguments["name"], arguments["data"])
                return [TextContent(type="text", text=format_output(result))]

            elif name == "doc_delete":
                result = client.delete(arguments["doctype"], arguments["name"])
                return [TextContent(type="text", text=str(result))]

            elif name == "doc_count":
                filters = json.loads(arguments["filters"]) if arguments.get("filters") else None
                count = client.count_docs(arguments["doctype"], filters=filters)
                return [TextContent(type="text", text=f"Count: {count}")]

            elif name == "call":
                result = client.post_api(arguments["method"], params=arguments.get("params", {}))
                return [TextContent(type="text", text=format_output(result))]

            elif name == "meta_doctypes":
                filters = json.loads(arguments["filters"]) if arguments.get("filters") else None
                result = client.list_doctypes(filters=filters)
                return [TextContent(type="text", text=format_output(result))]

            elif name == "meta_reports":
                filters = json.loads(arguments["filters"]) if arguments.get("filters") else None
                result = client.list_reports(filters=filters)
                return [TextContent(type="text", text=format_output(result))]

            elif name == "run_report":
                result = client.run_report(arguments["report_name"], filters=arguments.get("filters"))
                columns = result.get("columns", [])
                data = result.get("result", result.get("data", []))
                rows = zip_report_rows(columns, data)
                return [TextContent(type="text", text=format_output(rows, date_format=date_fmt, number_format=num_fmt))]

            elif name == "get_schema":
                schema = client.get_schema(arguments["doctype"])
                fields = format_schema_fields(schema.get("fields", []), compact=arguments.get("compact", True))
                return [TextContent(type="text", text=format_output(fields))]

            elif name == "bulk_create":
                results = client.bulk_create(arguments["doctype"], arguments["records"])
                return [TextContent(type="text", text=format_bulk_summary(results))]

            elif name == "bulk_update":
                results = client.bulk_update(arguments["doctype"], arguments["records"])
                return [TextContent(type="text", text=format_bulk_summary(results))]

            elif name == "bulk_delete":
                results = client.bulk_delete(arguments["doctype"], arguments["names"])
                return [TextContent(type="text", text=format_bulk_summary(results))]

            elif name == "check_connection":
                user = client.check_connection()
                return [TextContent(type="text", text=f"Connected as: {user}")]

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

        except Exception as e:
            return [TextContent(type="text", text=f"Error: {e}")]

    return server


# ---------------------------------------------------------------------------
# Transport entry points (T030 stdio, T031 HTTP)
# ---------------------------------------------------------------------------

def run_stdio():
    """Run the MCP server over stdio transport (blocking)."""
    import asyncio
    try:
        from mcp.server.stdio import stdio_server
    except ImportError as exc:
        raise ImportError("The 'mcp' package is required.") from exc

    server = _build_mcp_server()

    async def _main():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    asyncio.run(_main())


def run_http(port: int = 8765):
    """Run the MCP server over HTTP/SSE transport (blocking)."""
    import asyncio
    try:
        import uvicorn
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route
    except ImportError as exc:
        raise ImportError(
            "HTTP transport requires 'uvicorn', 'starlette', and 'mcp[sse]'. "
            "Install them with: pip install uvicorn starlette mcp"
        ) from exc

    server = _build_mcp_server()
    sse = SseServerTransport("/messages")

    async def handle_sse(request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await server.run(streams[0], streams[1], server.create_initialization_options())

    async def handle_messages(request):
        await sse.handle_post_message(request.scope, request.receive, request._send)

    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages", app=handle_messages),
        ]
    )
    uvicorn.run(app, host="0.0.0.0", port=port)


# ---------------------------------------------------------------------------
# Daemon runner (T032)
# ---------------------------------------------------------------------------

def _spawn_daemon(port: int) -> int:
    """Spawn the MCP HTTP server as a detached background daemon.

    Returns the PID of the spawned process.
    """
    cmd = [sys.executable, "-m", "frappe_cli.mcp_server", "--daemon-http", str(port)]

    kwargs = {}
    if sys.platform == "win32":
        # Windows: use DETACHED_PROCESS flag
        DETACHED_PROCESS = 0x00000008
        kwargs["creationflags"] = DETACHED_PROCESS
    else:
        # POSIX: start a new session
        kwargs["start_new_session"] = True

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **kwargs,
    )
    return proc.pid


def start_mcp_server(transport: str = "stdio", port: int = 8765, detach: bool = False):
    """Start the MCP server with the given transport.

    Args:
        transport: 'stdio' or 'http'.
        port: TCP port when using HTTP transport.
        detach: When True, spawn the server as a background daemon.
    """
    if detach:
        status = get_daemon_status()
        if status["running"]:
            print(f"MCP daemon already running (PID {status['pid']}).")
            return

        pid = _spawn_daemon(port)
        _save_state({"pid": pid, "port": port, "transport": "http"})
        print(f"MCP daemon started (PID {pid}, port {port}).")
        return

    if transport == "stdio":
        run_stdio()
    elif transport == "http":
        run_http(port=port)
    else:
        raise ValueError(f"Unknown transport: {transport!r}")


# ---------------------------------------------------------------------------
# __main__ entry point (used by daemon self-spawn)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Internal use: python -m frappe_cli.mcp_server --daemon-http <port>
    if len(sys.argv) == 3 and sys.argv[1] == "--daemon-http":
        run_http(port=int(sys.argv[2]))
    else:
        run_stdio()
