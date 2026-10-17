"""Public, stable failure categories used by the command-line interface."""

class EnhancementError(ValueError):
    """An input, source, output, or integrity invariant could not be proved."""


class UnsupportedStructure(EnhancementError):
    """GNATdoc syntax or Ada construct lies outside the qualified adapter."""
