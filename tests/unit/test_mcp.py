"""
T028: Unit tests for MCP tool calls and daemon control operations.
"""
import json
import os
import pytest
from unittest.mock import patch, MagicMock, mock_open


# ---------------------------------------------------------------------------
# Daemon state helpers
# ---------------------------------------------------------------------------

class TestDaemonState:
    def test_get_daemon_status_no_state_file(self, tmp_path):
        """Returns not running when state file doesn't exist."""
        from frappe_cli.mcp_server import _load_state, get_daemon_status
        with patch("frappe_cli.mcp_server._MCP_STATE_FILE", str(tmp_path / "mcp.json")):
            status = get_daemon_status()
        assert status["running"] is False
        assert status["pid"] is None

    def test_get_daemon_status_stale_pid(self, tmp_path):
        """Returns not running and clears state when PID is dead."""
        state_file = str(tmp_path / "mcp.json")
        with open(state_file, "w") as f:
            json.dump({"pid": 999999999, "port": 8765}, f)

        from frappe_cli.mcp_server import get_daemon_status
        with patch("frappe_cli.mcp_server._MCP_STATE_FILE", state_file):
            with patch("os.kill", side_effect=ProcessLookupError):
                status = get_daemon_status()

        assert status["running"] is False

    def test_get_daemon_status_live_pid(self, tmp_path):
        """Returns running when PID is alive."""
        state_file = str(tmp_path / "mcp.json")
        with open(state_file, "w") as f:
            json.dump({"pid": 12345, "port": 8765}, f)

        from frappe_cli.mcp_server import get_daemon_status
        with patch("frappe_cli.mcp_server._MCP_STATE_FILE", state_file):
            with patch("os.kill", return_value=None):  # No exception = alive
                status = get_daemon_status()

        assert status["running"] is True
        assert status["pid"] == 12345
        assert status["port"] == 8765

    def test_save_and_load_state(self, tmp_path):
        """State roundtrip via _save_state / _load_state."""
        state_file = str(tmp_path / "mcp.json")
        from frappe_cli.mcp_server import _save_state, _load_state

        with patch("frappe_cli.mcp_server._MCP_STATE_FILE", state_file), \
             patch("frappe_cli.mcp_server._MCP_STATE_DIR", str(tmp_path)):
            _save_state({"pid": 1234, "port": 9000})
            loaded = _load_state()

        assert loaded["pid"] == 1234
        assert loaded["port"] == 9000

    def test_clear_state(self, tmp_path):
        """_clear_state removes the state file."""
        state_file = str(tmp_path / "mcp.json")
        with open(state_file, "w") as f:
            json.dump({"pid": 1}, f)

        from frappe_cli.mcp_server import _clear_state
        with patch("frappe_cli.mcp_server._MCP_STATE_FILE", state_file):
            _clear_state()

        assert not os.path.exists(state_file)


# ---------------------------------------------------------------------------
# stop_daemon
# ---------------------------------------------------------------------------

class TestStopDaemon:
    def test_stop_running_daemon(self, tmp_path):
        """stop_daemon sends SIGTERM and clears state."""
        state_file = str(tmp_path / "mcp.json")
        with open(state_file, "w") as f:
            json.dump({"pid": 12345, "port": 8765}, f)

        from frappe_cli.mcp_server import stop_daemon
        with patch("frappe_cli.mcp_server._MCP_STATE_FILE", state_file), \
             patch("frappe_cli.mcp_server._MCP_STATE_DIR", str(tmp_path)), \
             patch("os.kill", return_value=None) as mock_kill:
            result = stop_daemon()

        assert result is True
        import signal
        mock_kill.assert_called_once_with(12345, signal.SIGTERM)
        assert not os.path.exists(state_file)

    def test_stop_no_daemon(self, tmp_path):
        """stop_daemon returns False when no daemon is running."""
        from frappe_cli.mcp_server import stop_daemon
        with patch("frappe_cli.mcp_server._MCP_STATE_FILE", str(tmp_path / "mcp.json")):
            result = stop_daemon()

        assert result is False

    def test_stop_stale_pid(self, tmp_path):
        """stop_daemon returns False and clears state for stale PID."""
        state_file = str(tmp_path / "mcp.json")
        with open(state_file, "w") as f:
            json.dump({"pid": 999999999}, f)

        from frappe_cli.mcp_server import stop_daemon
        with patch("frappe_cli.mcp_server._MCP_STATE_FILE", state_file), \
             patch("frappe_cli.mcp_server._MCP_STATE_DIR", str(tmp_path)), \
             patch("os.kill", side_effect=ProcessLookupError):
            result = stop_daemon()

        assert result is False


# ---------------------------------------------------------------------------
# start_mcp_server — detach mode
# ---------------------------------------------------------------------------

class TestStartMcpServerDaemon:
    def test_start_detached_spawns_process(self, tmp_path):
        """start_mcp_server with detach=True spawns a subprocess and saves state."""
        state_file = str(tmp_path / "mcp.json")

        from frappe_cli.mcp_server import start_mcp_server
        with patch("frappe_cli.mcp_server._MCP_STATE_FILE", state_file), \
             patch("frappe_cli.mcp_server._MCP_STATE_DIR", str(tmp_path)), \
             patch("frappe_cli.mcp_server.get_daemon_status", return_value={"running": False}), \
             patch("frappe_cli.mcp_server._spawn_daemon", return_value=9999) as mock_spawn, \
             patch("frappe_cli.mcp_server._save_state") as mock_save:
            start_mcp_server(transport="http", port=8765, detach=True)

        mock_spawn.assert_called_once_with(8765)
        mock_save.assert_called_once_with({"pid": 9999, "port": 8765, "transport": "http"})

    def test_start_detached_already_running(self, tmp_path, capsys):
        """start_mcp_server with detach=True does not spawn if already running."""
        from frappe_cli.mcp_server import start_mcp_server
        with patch("frappe_cli.mcp_server.get_daemon_status",
                   return_value={"running": True, "pid": 1234}), \
             patch("frappe_cli.mcp_server._spawn_daemon") as mock_spawn:
            start_mcp_server(transport="http", port=8765, detach=True)

        mock_spawn.assert_not_called()


# ---------------------------------------------------------------------------
# CLI mcp commands
# ---------------------------------------------------------------------------

class TestMcpCLICommands:
    def test_mcp_status_running(self):
        from click.testing import CliRunner
        from frappe_cli.cli import main

        runner = CliRunner()
        with patch("frappe_cli.mcp_server.get_daemon_status",
                   return_value={"running": True, "pid": 1234, "port": 8765}):
            result = runner.invoke(main, ["mcp", "status"])

        assert result.exit_code == 0
        assert "running" in result.output.lower()
        assert "1234" in result.output

    def test_mcp_status_not_running(self):
        from click.testing import CliRunner
        from frappe_cli.cli import main

        runner = CliRunner()
        with patch("frappe_cli.mcp_server.get_daemon_status",
                   return_value={"running": False, "pid": None, "port": None}):
            result = runner.invoke(main, ["mcp", "status"])

        assert result.exit_code == 0
        assert "not running" in result.output.lower()

    def test_mcp_stop_running_daemon(self):
        from click.testing import CliRunner
        from frappe_cli.cli import main

        runner = CliRunner()
        with patch("frappe_cli.mcp_server.stop_daemon", return_value=True):
            result = runner.invoke(main, ["mcp", "stop"])

        assert result.exit_code == 0
        assert "stopped" in result.output.lower()

    def test_mcp_stop_no_daemon(self):
        from click.testing import CliRunner
        from frappe_cli.cli import main

        runner = CliRunner()
        with patch("frappe_cli.mcp_server.stop_daemon", return_value=False):
            result = runner.invoke(main, ["mcp", "stop"])

        assert result.exit_code == 0
        assert "not running" in result.output.lower()
