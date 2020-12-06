from unittest import mock

from click.testing import CliRunner

from footbot.cli import cli
from footbot.main import app


def test_usage():
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_serve():
    with mock.patch.object(app, "run") as serve:
        runner = CliRunner()
        result = runner.invoke(cli, ["serve"])
        assert result.exit_code == 0
        serve.assert_called_once_with(host="0.0.0.0", port=8022, debug=True)


def test_optimise_team():
    with mock.patch("footbot.cli.optimise_entry") as optimise_entry:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "optimise",
                "1234",
                "5",
                "--end-event=6",
                "--total-budget=1",
                "--bench-factor=2",
                "--transfer-penalty=3",
                "--transfer-limit=4",
            ],
        )
        assert result.exit_code == 0
        optimise_entry.assert_called_once_with(
            1234,
            total_budget=1,
            bench_factor=2.0,
            transfer_penalty=3.0,
            transfer_limit=4,
            start_event=5,
            end_event=6,
            login=None,
            password=None,
        )
