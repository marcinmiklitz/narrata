import json

import pytest

from narrata.exceptions import UnsupportedFormatError
from narrata.formatting.serializers import format_sections, to_json, to_markdown_kv, to_plain, to_toon


def test_to_plain_joins_non_empty_lines() -> None:
    assert to_plain(["a", "", "b"]) == "a\nb"


def test_to_markdown_kv_preserves_insertion_order() -> None:
    output = to_markdown_kv({"summary": "x", "sparkline": "y"})
    assert output == "**summary**: x\n**sparkline**: y"


def test_to_toon_returns_string() -> None:
    output = to_toon({"summary": "x"})
    assert isinstance(output, str)
    assert output


def test_format_sections_plain() -> None:
    result = format_sections({"summary": "s", "sparkline": "p"}, output_format="plain")
    assert result == "s\np"


def test_format_sections_markdown_kv() -> None:
    result = format_sections({"summary": "s"}, output_format="markdown_kv")
    assert result == "**summary**: s"


def test_to_json_returns_valid_json() -> None:
    data = {"overview": "AAPL (100 pts)", "regime": "Uptrend"}
    output = to_json(data)
    parsed = json.loads(output)
    assert parsed == data


def test_to_json_handles_unicode() -> None:
    data = {"price": "100 → 200"}
    output = to_json(data)
    assert "→" in output


def test_to_toon_preserves_keys() -> None:
    data = {"overview": "AAPL", "regime": "Uptrend"}
    output = to_toon(data)
    assert "overview" in output
    assert "AAPL" in output


def test_to_markdown_kv_multiline_value() -> None:
    data = {"indicators": "RSI: 40\nMACD: bearish"}
    output = to_markdown_kv(data)
    assert "**indicators**: RSI: 40\nMACD: bearish" == output


def test_to_plain_skips_empty_lines() -> None:
    assert to_plain(["a", "", "", "b", ""]) == "a\nb"


def test_format_sections_toon() -> None:
    result = format_sections({"summary": "s", "regime": "r"}, output_format="toon")
    assert "summary" in result
    assert "regime" in result


def test_format_sections_json() -> None:
    result = format_sections({"summary": "s", "regime": "r"}, output_format="json")
    parsed = json.loads(result)
    assert parsed == {"summary": "s", "regime": "r"}


def test_format_sections_unsupported_format_raises() -> None:
    with pytest.raises(UnsupportedFormatError):
        format_sections({"summary": "s"}, output_format="invalid")  # type: ignore[arg-type]
