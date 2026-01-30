import json
from unittest.mock import MagicMock, patch

import numpy as np

from oco_viz.data.oco3 import (
    filter_quality,
    granule_download_urls,
    search_granules,
)


def _mock_cmr_response(n_entries: int = 3) -> bytes:
    entries = [
        {
            "title": f"oco3_LtCO2_{i:06d}.nc4",
            "id": f"G{i}",
            "links": [
                {"href": f"https://data.example.com/oco3_{i:06d}.nc4"},
                {"href": f"https://opendap.example.com/oco3_{i:06d}.nc4"},
            ],
        }
        for i in range(n_entries)
    ]
    return json.dumps({"feed": {"entry": entries}}).encode()


def test_search_granules_returns_entries():
    mock_resp = MagicMock()
    mock_resp.read.return_value = _mock_cmr_response(2)
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        entries = search_granules("2024-01-01", "2024-01-31")

    assert len(entries) == 2
    assert "title" in entries[0]


def test_granule_download_urls_extracts_nc4():
    entries = [
        {"links": [
            {"href": "https://opendap.example.com/file.nc4"},
            {"href": "https://data.example.com/file.nc4"},
        ]},
        {"links": [
            {"href": "https://data.example.com/other.nc4"},
        ]},
    ]
    urls = granule_download_urls(entries)
    assert len(urls) == 2
    # Should skip opendap links
    assert all("opendap" not in u for u in urls)


def test_filter_quality_keeps_good_data():
    xco2 = np.array([400.0, 410.0, 420.0, 405.0])
    flags = np.array([0, 1, 0, 0], dtype=np.int8)
    filtered = filter_quality(xco2, flags)
    assert len(filtered) == 3
    np.testing.assert_array_equal(filtered, [400.0, 420.0, 405.0])
