from unittest.mock import patch
from frappe_cli.config import is_interactive


def test_is_interactive_true():
    with patch("sys.stdin.isatty", return_value=True), patch("sys.stdout.isatty", return_value=True):
        assert is_interactive() is True


def test_is_interactive_false_stdin():
    with patch("sys.stdin.isatty", return_value=False), patch("sys.stdout.isatty", return_value=True):
        assert is_interactive() is False


def test_is_interactive_false_stdout():
    with patch("sys.stdin.isatty", return_value=True), patch("sys.stdout.isatty", return_value=False):
        assert is_interactive() is False


@patch("frappe_cli.config.is_interactive", return_value=True)
def test_config_set_interactive_success(mock_interactive, tmp_path):
    from frappe_cli.cli import main
    from click.testing import CliRunner
    import json
    from unittest.mock import MagicMock

    temp_config = tmp_path / "config.json"

    with patch("frappe_cli.config.DEFAULT_CONFIG_PATH", str(temp_config)), \
         patch("InquirerPy.inquirer.text") as mock_text, \
         patch("InquirerPy.inquirer.secret") as mock_secret, \
         patch("InquirerPy.inquirer.select") as mock_select:

        # Setup mocks to return values sequentially
        mock_url_inst = MagicMock()
        mock_url_inst.execute.return_value = "mysite.com"

        mock_key_inst = MagicMock()
        mock_key_inst.execute.return_value = "mykey"

        mock_profile_inst = MagicMock()
        mock_profile_inst.execute.return_value = "myprofile"

        mock_text.side_effect = [mock_url_inst, mock_key_inst, mock_profile_inst]

        mock_sec_inst = MagicMock()
        mock_sec_inst.execute.return_value = "mysecret"
        mock_secret.return_value = mock_sec_inst

        mock_date_inst = MagicMock()
        mock_date_inst.execute.return_value = "french"

        mock_num_inst = MagicMock()
        mock_num_inst.execute.return_value = "german"

        mock_select.side_effect = [mock_date_inst, mock_num_inst]

        runner = CliRunner()
        res = runner.invoke(main, ["config", "set"])

        assert res.exit_code == 0
        assert "Configuration saved successfully" in res.output

        # Verify JSON
        with open(temp_config) as f:
            cfg = json.load(f)
            assert cfg["profiles"]["myprofile"]["site_url"] == "https://mysite.com"
            assert cfg["profiles"]["myprofile"]["api_key"] == "mykey"
            assert cfg["profiles"]["myprofile"]["api_secret"] == "mysecret"
            assert cfg["profiles"]["myprofile"]["date_format"] == "french"
            assert cfg["profiles"]["myprofile"]["number_format"] == "german"


@patch("frappe_cli.config.is_interactive", return_value=True)
def test_config_use_interactive_success(mock_interactive, tmp_path):
    from frappe_cli.cli import main
    from click.testing import CliRunner
    import json
    from unittest.mock import MagicMock

    temp_config = tmp_path / "config.json"
    # Pre-populate config
    with open(temp_config, "w") as f:
        json.dump({
            "default_profile": "dev",
            "profiles": {
                "dev": {"site_url": "https://dev.site", "api_key": "k", "api_secret": "s"},
                "prod": {"site_url": "https://prod.site", "api_key": "k", "api_secret": "s"}
            }
        }, f)

    with patch("frappe_cli.config.DEFAULT_CONFIG_PATH", str(temp_config)), \
         patch("InquirerPy.inquirer.select") as mock_select:

        mock_sel_inst = MagicMock()
        mock_sel_inst.execute.return_value = "prod"
        mock_select.return_value = mock_sel_inst

        runner = CliRunner()
        res = runner.invoke(main, ["config", "use"])

        assert res.exit_code == 0
        assert "Default profile set to 'prod'." in res.output

        with open(temp_config) as f:
            cfg = json.load(f)
            assert cfg["default_profile"] == "prod"


@patch("frappe_cli.config.is_interactive", return_value=True)
def test_config_remove_interactive_success(mock_interactive, tmp_path):
    from frappe_cli.cli import main
    from click.testing import CliRunner
    import json
    from unittest.mock import MagicMock

    temp_config = tmp_path / "config.json"
    with open(temp_config, "w") as f:
        json.dump({
            "default_profile": "dev",
            "profiles": {
                "dev": {"site_url": "https://dev.site", "api_key": "k", "api_secret": "s"},
                "prod": {"site_url": "https://prod.site", "api_key": "k", "api_secret": "s"}
            }
        }, f)

    with patch("frappe_cli.config.DEFAULT_CONFIG_PATH", str(temp_config)), \
         patch("InquirerPy.inquirer.select") as mock_select, \
         patch("InquirerPy.inquirer.confirm") as mock_confirm:

        mock_sel_inst = MagicMock()
        mock_sel_inst.execute.return_value = "prod"
        mock_select.return_value = mock_sel_inst

        mock_conf_inst = MagicMock()
        mock_conf_inst.execute.return_value = True
        mock_confirm.return_value = mock_conf_inst

        runner = CliRunner()
        res = runner.invoke(main, ["config", "remove"])

        assert res.exit_code == 0
        assert "Profile 'prod' removed successfully." in res.output

        with open(temp_config) as f:
            cfg = json.load(f)
            assert "prod" not in cfg["profiles"]


@patch("frappe_cli.config.is_interactive", return_value=True)
def test_config_remove_interactive_cancel(mock_interactive, tmp_path):
    from frappe_cli.cli import main
    from click.testing import CliRunner
    import json
    from unittest.mock import MagicMock

    temp_config = tmp_path / "config.json"
    with open(temp_config, "w") as f:
        json.dump({
            "default_profile": "dev",
            "profiles": {
                "dev": {"site_url": "https://dev.site", "api_key": "k", "api_secret": "s"},
                "prod": {"site_url": "https://prod.site", "api_key": "k", "api_secret": "s"}
            }
        }, f)

    with patch("frappe_cli.config.DEFAULT_CONFIG_PATH", str(temp_config)), \
         patch("InquirerPy.inquirer.select") as mock_select, \
         patch("InquirerPy.inquirer.confirm") as mock_confirm:

        mock_sel_inst = MagicMock()
        mock_sel_inst.execute.return_value = "prod"
        mock_select.return_value = mock_sel_inst

        mock_conf_inst = MagicMock()
        mock_conf_inst.execute.return_value = False
        mock_confirm.return_value = mock_conf_inst

        runner = CliRunner()
        res = runner.invoke(main, ["config", "remove"])

        assert res.exit_code == 0
        assert "Operation canceled." in res.output

        with open(temp_config) as f:
            cfg = json.load(f)
            assert "prod" in cfg["profiles"]


@patch("frappe_cli.config.is_interactive", return_value=False)
def test_config_set_non_tty_fails(mock_interactive, tmp_path):
    from frappe_cli.cli import main
    from click.testing import CliRunner

    runner = CliRunner()
    res = runner.invoke(main, ["config", "set"])

    assert res.exit_code == 1
    assert "Input is not a TTY. Interactive prompts are unavailable." in res.output


@patch("frappe_cli.config.is_interactive", return_value=False)
def test_config_use_non_tty_fails(mock_interactive, tmp_path):
    from frappe_cli.cli import main
    from click.testing import CliRunner

    runner = CliRunner()
    res = runner.invoke(main, ["config", "use"])

    assert res.exit_code == 1
    assert "Input is not a TTY. Interactive prompts are unavailable." in res.output


@patch("frappe_cli.config.is_interactive", return_value=False)
def test_config_remove_non_tty_fails(mock_interactive, tmp_path):
    from frappe_cli.cli import main
    from click.testing import CliRunner

    runner = CliRunner()
    res = runner.invoke(main, ["config", "remove"])

    assert res.exit_code == 1
    assert "Input is not a TTY. Interactive prompts are unavailable." in res.output


@patch("frappe_cli.config.is_interactive", return_value=True)
def test_config_set_interactive_cancel(mock_interactive, tmp_path):
    from frappe_cli.cli import main
    from click.testing import CliRunner

    temp_config = tmp_path / "config.json"

    with patch("frappe_cli.config.DEFAULT_CONFIG_PATH", str(temp_config)), \
         patch("InquirerPy.inquirer.text", side_effect=KeyboardInterrupt):

        runner = CliRunner()
        res = runner.invoke(main, ["config", "set"])

        assert res.exit_code == 1
        assert "Operation canceled." in res.output
