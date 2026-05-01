import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path


SERVICE_DIR = Path(__file__).resolve().parents[1] / "services" / "generator"


def load_module():
    for name in list(sys.modules):
        if name == "src" or name.startswith("src."):
            del sys.modules[name]
    sys.path.insert(0, str(SERVICE_DIR))
    try:
        return importlib.import_module("src.generate_events")
    finally:
        sys.path.remove(str(SERVICE_DIR))


def test_make_event_has_required_fields_without_campaign(monkeypatch):
    module = load_module()
    monkeypatch.setattr(module.random, "choices", lambda *args, **kwargs: ["view"])
    monkeypatch.setattr(module.random, "choice", lambda values: values[0])
    monkeypatch.setattr(module.random, "randint", lambda start, end: start)

    ts = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    event = module.make_event(ts, source_version="v-test", allow_campaign=False)

    assert event["event_id"]
    assert event["user_id"] == 1
    assert event["event_type"] == "view"
    assert event["event_ts"] == ts.isoformat()
    assert event["device_type"] == "ios"
    assert event["price"] is None
    assert event["currency"] == "USD"
    assert event["source_version"] == "v-test"
    assert event["geo_country"] == "US"
    assert "campaign_id" not in event


def test_purchase_event_gets_price(monkeypatch):
    module = load_module()
    monkeypatch.setattr(module.random, "choices", lambda *args, **kwargs: ["purchase"])
    monkeypatch.setattr(module.random, "choice", lambda values: values[-1])
    monkeypatch.setattr(module.random, "randint", lambda start, end: end)

    ts = datetime(2026, 5, 1, tzinfo=timezone.utc)
    event = module.make_event(ts, source_version="v1", allow_campaign=False)

    assert event["event_type"] == "purchase"
    assert event["price"] == 99.99


def test_campaign_field_only_appears_when_allowed(monkeypatch):
    module = load_module()
    monkeypatch.setattr(module.random, "choices", lambda *args, **kwargs: ["add_to_cart"])
    monkeypatch.setattr(module.random, "choice", lambda values: values[1])
    monkeypatch.setattr(module.random, "randint", lambda start, end: start)

    event = module.make_event(datetime(2026, 5, 1, tzinfo=timezone.utc), "v1", allow_campaign=True)

    assert "campaign_id" in event
    assert event["campaign_id"] == "spring_1"
