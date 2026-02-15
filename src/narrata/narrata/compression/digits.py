"""Digit-level tokenization utilities.

References:
    [LLMTime] Gruver et al., "Large Language Models Are Zero-Shot
    Time Series Forecasters", NeurIPS 2023. arXiv:2310.07820
"""

import re

_DIGIT_PATTERN = re.compile(r"(\d)")


def digit_tokenize(text: str, add_note: bool = True) -> str:
    """Split every digit into standalone tokens separated by spaces.

    :param text: Input text.
    :param add_note: Prefix output with a short marker when digit splitting is applied.
    :return: Digit-tokenized text.
    """
    spaced = _DIGIT_PATTERN.sub(r" \1 ", text)
    tokenized = " ".join(spaced.split())
    if add_note:
        return f"<digits-split>\n{tokenized}"
    return tokenized
