import sys

from hermes_kit.cli import main


def test_cli_no_args(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["hermes-kit"])
    try:
        main()
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert "Usage:" in captured.out or "Usage:" in captured.err


def test_cli_list(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["hermes-kit", "list"])
    try:
        main()
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert "router" in captured.out
    assert "fallback" in captured.out
