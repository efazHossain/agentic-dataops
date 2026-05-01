import importlib
import json
import sys
from pathlib import Path


SERVICE_DIR = Path(__file__).resolve().parents[1] / "services" / "loader"


def load_module():
    for name in list(sys.modules):
        if name == "src" or name.startswith("src."):
            del sys.modules[name]
    sys.path.insert(0, str(SERVICE_DIR))
    try:
        return importlib.import_module("src.load_events")
    finally:
        sys.path.remove(str(SERVICE_DIR))


def test_event_to_row_maps_expected_column_order():
    module = load_module()
    event = {
        "event_id": "evt-1",
        "user_id": 42,
        "event_type": "purchase",
        "event_ts": "2026-05-01T00:00:00+00:00",
        "device_type": "web",
        "price": 49.99,
        "currency": "USD",
        "source_version": "v1",
        "geo_country": "US",
        "campaign_id": "spring_1",
    }

    assert module.event_to_row(event) == (
        "evt-1",
        42,
        "purchase",
        "2026-05-01T00:00:00+00:00",
        "web",
        49.99,
        "USD",
        "v1",
        "US",
        "spring_1",
    )


def test_event_to_row_defaults_missing_optional_fields_to_none():
    module = load_module()

    assert module.event_to_row({"event_id": "evt-1"}) == (
        "evt-1",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )


def test_parse_jsonl_lines_ignores_blank_lines():
    module = load_module()
    event = {
        "event_id": "evt-1",
        "user_id": 7,
        "event_type": "view",
        "event_ts": "2026-05-01T00:00:00+00:00",
        "device_type": "ios",
    }

    rows = module.parse_jsonl_lines(["", "   ", json.dumps(event)])

    assert len(rows) == 1
    assert rows[0][0] == "evt-1"
    assert rows[0][1] == 7
    assert rows[0][2] == "view"
