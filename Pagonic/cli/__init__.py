"""Command-line interface for Pagonic."""

from Pagonic import __version__

__all__ = ["cli"]


def __getattr__(name):
    """Load the Click application only when the compatibility export is used."""
    if name != "cli":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from .main import cli

    globals()[name] = cli
    return cli
