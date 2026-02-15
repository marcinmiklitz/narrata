import pytest

from narrata.exceptions import UnsupportedFormatError
from narrata.formatting.serializers import format_sections, to_markdown_kv, to_plain, to_toon


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


def test_format_sections_unsupported_format_raises() -> None:
    with pytest.raises(UnsupportedFormatError):
        format_sections({"summary": "s"}, output_format="invalid")  # type: ignore[arg-type]
