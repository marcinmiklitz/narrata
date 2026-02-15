from narrata.compression.digits import digit_tokenize


def test_digit_tokenize_splits_digits() -> None:
    assert digit_tokenize("Price: 171.24") == "<digits-split>\nPrice: 1 7 1 . 2 4"


def test_digit_tokenize_collapses_whitespace() -> None:
    assert digit_tokenize("A  10  B") == "<digits-split>\nA 1 0 B"


def test_digit_tokenize_leaves_text_without_digits_unchanged() -> None:
    assert digit_tokenize("No numbers here.") == "<digits-split>\nNo numbers here."


def test_digit_tokenize_without_note() -> None:
    assert digit_tokenize("No numbers here.", add_note=False) == "No numbers here."
