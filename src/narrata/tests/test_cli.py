from pathlib import Path

import pytest

from narrata.cli import main

ASSETS_DIR = Path(__file__).parent / "assets"
AAPL_CSV = str(ASSETS_DIR / "aapl_1y.csv")
MSFT_CSV = str(ASSETS_DIR / "msft_1y.csv")


def test_narrate_csv_default(capsys: pytest.CaptureFixture[str]) -> None:
    main([AAPL_CSV])
    out = capsys.readouterr().out
    assert "Date range:" in out
    assert "Range:" in out


def test_narrate_with_ticker(capsys: pytest.CaptureFixture[str]) -> None:
    main([AAPL_CSV, "--ticker", "AAPL"])
    out = capsys.readouterr().out
    assert "AAPL" in out


def test_narrate_json_format(capsys: pytest.CaptureFixture[str]) -> None:
    import json

    main([AAPL_CSV, "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "overview" in data


def test_narrate_markdown_kv_format(capsys: pytest.CaptureFixture[str]) -> None:
    main([AAPL_CSV, "--format", "markdown_kv"])
    out = capsys.readouterr().out
    assert "**overview**:" in out


def test_narrate_toon_format(capsys: pytest.CaptureFixture[str]) -> None:
    main([AAPL_CSV, "--format", "toon"])
    out = capsys.readouterr().out
    assert "overview" in out


def test_narrate_disable_sections(capsys: pytest.CaptureFixture[str]) -> None:
    main([AAPL_CSV, "--no-regime", "--no-indicators", "--no-symbolic"])
    out = capsys.readouterr().out
    assert "Date range:" in out
    assert "Regime:" not in out
    assert "RSI" not in out
    assert "SAX" not in out


def test_narrate_tsv_input(capsys: pytest.CaptureFixture[str]) -> None:
    tsv_path = str(ASSETS_DIR / "AAPL.tsv")
    main([tsv_path])
    out = capsys.readouterr().out
    assert "Date range:" in out


def test_narrate_parquet_input(capsys: pytest.CaptureFixture[str]) -> None:
    pq_path = str(ASSETS_DIR / "AAPL.parquet")
    main([pq_path])
    out = capsys.readouterr().out
    assert "Date range:" in out


def test_narrate_verbose_flag(capsys: pytest.CaptureFixture[str]) -> None:
    main([AAPL_CSV, "--verbose"])
    out = capsys.readouterr().out
    assert "Date range:" in out


def test_narrate_currency_and_precision(capsys: pytest.CaptureFixture[str]) -> None:
    main([AAPL_CSV, "--currency", "$", "--precision", "0"])
    out = capsys.readouterr().out
    assert "$" in out


def test_compare_two_files(capsys: pytest.CaptureFixture[str]) -> None:
    main(["compare", AAPL_CSV, MSFT_CSV])
    out = capsys.readouterr().out
    assert "→" in out
    assert "Price:" in out


def test_compare_json_format(capsys: pytest.CaptureFixture[str]) -> None:
    import json

    main(["compare", AAPL_CSV, MSFT_CSV, "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, dict)


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit, match="0"):
        main(["--version"])
    out = capsys.readouterr().out
    assert "narrata" in out


def test_parquet_stdin_rejected() -> None:
    with pytest.raises(SystemExit, match="parquet"):
        main(["-", "--input-format", "parquet"])
