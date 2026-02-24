import json
import os
import random
import uuid
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from src.write_to_minio import write_jsonl_to_minio

EVENT_TYPES = ["view", "add_to_cart", "purchase"]
DEVICES = ["ios", "android", "web"]

def _rand_price(event_type: str):
    if event_type != "purchase":
        return None
    return round(random.choice([9.99, 14.99, 19.99, 29.99, 49.99, 79.99, 99.99]), 2)

def make_event(ts: datetime, source_version: str, allow_campaign: bool) -> dict:
    event_type = random.choices(EVENT_TYPES, weights=[0.78, 0.17, 0.05], k=1)[0]
    evt = {
        "event_id": str(uuid.uuid4()),
        "user_id": random.randint(1, 50_000),
        "event_type": event_type,
        "event_ts": ts.isoformat(),
        "device_type": random.choice(DEVICES),
        "price": _rand_price(event_type),
        "currency": "USD",
        "source_version": source_version,
        "geo_country": random.choice(["US", "CA", "MX", "GB", "DE", "IN"]),
    }
    if allow_campaign:
        evt["campaign_id"] = random.choice([None, "spring_1", "spring_2", "retarget_7"])
    return evt

def main() -> None:
    bucket = os.getenv("GEN_BUCKET", "lake-raw")
    prefix = os.getenv("GEN_PREFIX", "events")
    dt_str = os.getenv("GEN_DATE")  # YYYY-MM-DD
    n = int(os.getenv("GEN_N", "5000"))
    source_version = os.getenv("GEN_SOURCE_VERSION", "v1")
    allow_campaign = os.getenv("GEN_ALLOW_CAMPAIGN", "0") == "1"

    dt = datetime.now(timezone.utc).date() if not dt_str else datetime.fromisoformat(dt_str).date()

    events = []
    for _ in range(n):
        ts = datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc) + relativedelta(
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )
        events.append(make_event(ts, source_version, allow_campaign))

    key = f"{prefix}/dt={dt.isoformat()}/events_{dt.isoformat()}.jsonl"
    body = "\n".join(json.dumps(e) for e in events) + "\n"

    write_jsonl_to_minio(bucket=bucket, key=key, data=body.encode("utf-8"))
    print(f"Wrote {len(events)} events to s3://{bucket}/{key}")

if __name__ == "__main__":
    main()
