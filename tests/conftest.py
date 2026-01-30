"""Shared pytest configuration and hooks."""

from __future__ import annotations

import os

import pytest

_ON_CI = os.environ.get("CI") == "true"


def pytest_collection_modifyitems(_config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-skip tests marked with @pytest.mark.skipci on CI."""
    if not _ON_CI:
        return
    skip = pytest.mark.skip(reason="VTK EGL segfaults on headless CI")
    for item in items:
        if "skipci" in item.keywords:
            item.add_marker(skip)
