"""Tests for the fused OCO-2/OCO-3 data module."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from oco_viz.data.oco import find_nearest_passes, search_multi_satellite


def _mock_cmr_response(
    n_entries: int = 3,
    *,
    title_prefix: str = "oco3_LtCO2",
    base_date: str = "2025-03-15",
) -> bytes:
    """Build a fake CMR JSON response with *n_entries* granules."""
    entries = [
        {
            "title": f"{title_prefix}_{i:06d}.nc4",
            "id": f"G{i}",
            "time_start": f"{base_date}T00:00:00.000Z",
            "links": [
                {"href": f"https://data.example.com/{title_prefix}_{i:06d}.nc4"},
            ],
        }
        for i in range(n_entries)
    ]
    return json.dumps({"feed": {"entry": entries}}).encode()


def _urlopen_side_effect(collection_to_entries: dict[str, bytes]):
    """Return a side_effect callable that maps CMR collection_id → response."""

    def _side_effect(req):  # type: ignore[no-untyped-def]
        url = req.full_url if hasattr(req, "full_url") else str(req)
        for coll_id, data in collection_to_entries.items():
            if coll_id in url:
                mock_resp = MagicMock()
                mock_resp.read.return_value = data
                mock_resp.__enter__ = lambda s: s
                mock_resp.__exit__ = MagicMock(return_value=False)
                return mock_resp
        # Fallback: empty feed
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"feed": {"entry": []}}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    return _side_effect


# ---------------------------------------------------------------------------
# find_nearest_passes
# ---------------------------------------------------------------------------


def test_find_nearest_passes_returns_sorted_by_distance() -> None:
    """Passes from both satellites, sorted by abs(days_from_target)."""
    oco3_data = _mock_cmr_response(2, title_prefix="oco3_LtCO2", base_date="2025-03-14")
    oco2_data = _mock_cmr_response(1, title_prefix="oco2_LtCO2", base_date="2025-03-16")

    side_effect = _urlopen_side_effect(
        {
            "C2910086168-GES_DISC": oco3_data,  # oco3
            "C2912085112-GES_DISC": oco2_data,  # oco2
        }
    )

    with patch("urllib.request.urlopen", side_effect=side_effect):
        passes = find_nearest_passes(-26.52, 29.17, "2025-03-15")

    assert len(passes) == 3
    # First entry should be closest (distance 1), not farthest
    distances = [abs(p["days_from_target"]) for p in passes]
    assert distances == sorted(distances)


def test_find_nearest_passes_single_satellite() -> None:
    """Can restrict to a single satellite."""
    oco2_data = _mock_cmr_response(2, title_prefix="oco2_LtCO2", base_date="2025-03-10")

    side_effect = _urlopen_side_effect(
        {
            "C2912085112-GES_DISC": oco2_data,
        }
    )

    with patch("urllib.request.urlopen", side_effect=side_effect):
        passes = find_nearest_passes(-26.52, 29.17, "2025-03-15", satellites=("oco2",))

    assert len(passes) == 2
    assert all(p["satellite"] == "oco2" for p in passes)


def test_find_nearest_passes_no_results() -> None:
    """Empty CMR feed returns empty list."""
    empty = json.dumps({"feed": {"entry": []}}).encode()
    side_effect = _urlopen_side_effect(
        {
            "C2910086168-GES_DISC": empty,
            "C2912085112-GES_DISC": empty,
        }
    )

    with patch("urllib.request.urlopen", side_effect=side_effect):
        passes = find_nearest_passes(-26.52, 29.17, "2025-03-15")

    assert passes == []


def test_find_nearest_passes_unknown_satellite_raises() -> None:
    with pytest.raises(ValueError, match="Unknown satellite"):
        find_nearest_passes(-26.52, 29.17, "2025-03-15", satellites=("oco9",))


# ---------------------------------------------------------------------------
# search_multi_satellite
# ---------------------------------------------------------------------------


def test_search_multi_satellite_merges_results() -> None:
    """Entries from both satellites are merged and tagged."""
    oco3_data = _mock_cmr_response(1, title_prefix="oco3_LtCO2", base_date="2025-03-14")
    oco2_data = _mock_cmr_response(1, title_prefix="oco2_LtCO2", base_date="2025-03-16")

    side_effect = _urlopen_side_effect(
        {
            "C2910086168-GES_DISC": oco3_data,
            "C2912085112-GES_DISC": oco2_data,
        }
    )

    with patch("urllib.request.urlopen", side_effect=side_effect):
        entries = search_multi_satellite("2025-03-01", "2025-03-31")

    assert len(entries) == 2
    satellites = {e["satellite"] for e in entries}
    assert satellites == {"oco3", "oco2"}
    # Sorted by time_start
    times = [e["time_start"] for e in entries]
    assert times == sorted(times)
