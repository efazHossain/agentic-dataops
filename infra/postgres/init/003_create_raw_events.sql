CREATE TABLE IF NOT EXISTS raw.raw_events (
  event_id       TEXT PRIMARY KEY,
  user_id        BIGINT,
  event_type     TEXT,
  event_ts       TIMESTAMPTZ,
  device_type    TEXT,
  price          NUMERIC(10,2),
  currency       TEXT,
  source_version TEXT,
  geo_country    TEXT,
  campaign_id    TEXT,
  ingested_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_raw_events_ts ON raw.raw_events (event_ts);
CREATE INDEX IF NOT EXISTS idx_raw_events_type ON raw.raw_events (event_type);
