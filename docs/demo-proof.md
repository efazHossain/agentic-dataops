# Demo Proof

This run demonstrates the full remediation loop working end to end in Docker Compose.

Run date: 2026-05-01

Command:

```bash
docker compose --profile tools run --rm agent
```

## Result Summary

The freshness agent successfully:

1. Detected stale dbt source freshness for `raw.raw_events`.
2. Generated a new event partition in MinIO.
3. Loaded the latest JSONL partition into Postgres.
4. Rebuilt dbt staging and mart models.
5. Ran dbt data tests.
6. Re-ran freshness and confirmed the source passed.
7. Logged the agent run to `ops.pipeline_runs`.

## Key Output

```text
[2026-05-01T02:37:49.772552+00:00] freshness=STALE -> remediate
generator_exit=0
latest_key=events/dt=2026-05-01/events_2026-05-01.jsonl
loader_exit=0
dbt_run_exit=0
dbt_test_exit=0
freshness_after_exit=0
```

## Freshness Before

```text
1 of 1 ERROR STALE freshness of raw.raw_events
Status: error
```

## Remediation

```text
Wrote 5000 events to s3://lake-raw/events/dt=2026-05-01/events_2026-05-01.jsonl

Loaded 5000 events from s3://lake-raw/events/dt=2026-05-01/events_2026-05-01.jsonl into raw.raw_events (deduped by event_id)
```

## dbt Run

```text
1 of 2 OK created sql view model staging.stg_events
2 of 2 OK created sql incremental model mart.fct_events_daily

Done. PASS=2 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=2
```

## dbt Tests

```text
Finished running 8 data tests
Completed successfully
Done. PASS=8 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=8
```

## Freshness After

```text
1 of 1 PASS freshness of raw.raw_events
```

## Verification Queries

```sql
SELECT COUNT(*) FROM raw.raw_events;

SELECT *
FROM mart.fct_events_daily
ORDER BY event_day DESC, event_count DESC
LIMIT 10;

SELECT run_id, pipeline_name, status, started_at, ended_at
FROM ops.pipeline_runs
ORDER BY started_at DESC
LIMIT 5;
```
