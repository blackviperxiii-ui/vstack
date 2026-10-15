"""Shared test helper: stand-in tiktoken module for environments without it."""

from __future__ import annotations

import sys
import types


def install_tiktoken_stub() -> None:
    """Register a minimal tiktoken in sys.modules if the real one is missing.

    Tests that need token counts patch get_encoding themselves.
    """
    try:
        import tiktoken  # noqa: F401
    except ImportError:
        stub = types.ModuleType("tiktoken")
        stub.Encoding = object  # type: ignore[attr-defined]
        stub.get_encoding = lambda name: None  # type: ignore[attr-defined]
        sys.modules["tiktoken"] = stub
