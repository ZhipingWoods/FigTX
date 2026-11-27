from figtx_forge.cli import main


def test_cli_version(capsys):
    assert main(["--version"]) == 0
    assert "0.1.0" in capsys.readouterr().out


def test_cli_validate_reports_errors(tmp_path, capsys):
    p = tmp_path / "s.json"
    p.write_text('{"version":1,"nodes":[]}')
    assert main(["validate", str(p)]) == 1
    assert "canvas" in capsys.readouterr().err
