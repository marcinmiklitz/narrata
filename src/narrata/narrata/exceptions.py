"""Custom exception hierarchy for narrata."""


class NarrataError(Exception):
    """Base exception for narrata."""


class ValidationError(NarrataError):
    """Raised when input data does not meet narrata contracts."""


class UnsupportedFormatError(NarrataError):
    """Raised when a requested output format is unsupported."""
