import narrata


def test_public_api_exports_expected_symbols() -> None:
    # Every symbol in __all__ must be actually importable from the package
    for sym in narrata.__all__:
        assert hasattr(narrata, sym), f"{sym!r} listed in __all__ but not importable"
    # Key symbols that must always be present
    for sym in (
        "narrate",
        "compare",
        "to_json",
        "to_plain",
        "to_markdown_kv",
        "to_toon",
        "format_sections",
        "from_ccxt",
        "from_coingecko",
        "normalize_columns",
        "validate_ohlcv_frame",
        "infer_frequency_label",
        "digit_tokenize",
        "make_sparkline",
    ):
        assert sym in narrata.__all__, f"{sym!r} missing from __all__"
