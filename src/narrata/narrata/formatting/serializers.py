"""Serializers for final narration output."""

from collections.abc import Mapping, Sequence

from toons import dumps

from narrata.exceptions import UnsupportedFormatError
from narrata.types import OutputFormat


def to_plain(lines: Sequence[str]) -> str:
    """Join non-empty lines into plain-text output.

    :param lines: Ordered lines to join.
    :return: Plain-text representation.
    """
    return "\n".join(line for line in lines if line)


def to_markdown_kv(data: Mapping[str, object]) -> str:
    """Serialize key-value pairs as Markdown.

    :param data: Mapping of section names to values.
    :return: Markdown key-value representation.
    """
    return "\n".join(f"**{key}**: {value}" for key, value in data.items())


def to_toon(data: Mapping[str, object]) -> str:
    """Serialize mappings to TOON.

    Requires the ``toons`` package.

    :param data: Mapping of section names to values.
    :return: TOON string representation.
    """
    return str(dumps(dict(data)))


def format_sections(sections: Mapping[str, str], output_format: OutputFormat = "plain") -> str:
    """Format narration sections for the selected output format.

    :param sections: Ordered mapping of section keys to rendered text.
    :param output_format: Output format selector.
    :return: Serialized text output.
    """
    if output_format == "plain":
        return to_plain(list(sections.values()))
    if output_format == "markdown_kv":
        return to_markdown_kv(sections)
    if output_format == "toon":
        return to_toon(sections)
    raise UnsupportedFormatError(f"Unsupported output format: {output_format}")
