# Agentic DataOps (Local-First)

> A local-first, production-style data platform with automated freshness monitoring and pipeline remediation.

This project demonstrates how to build a reproducible data platform using object storage, a warehouse, dbt transformations, and an autonomous agent that monitors and repairs pipeline state.

It is fully containerized and runs locally using Docker Compose.

---

## Overview

This system simulates a real-world analytics pipeline:

1. Event data is generated and written to object storage (MinIO).
2. Data is ingested into a warehouse (Postgres raw layer).
3. dbt transforms raw data into staging and mart models.
4. dbt tests validate data integrity.
5. An agent monitors freshness and automatically remediates stale pipelines.
6. Execution telemetry is logged into an ops schema.

This bridges traditional data engineering and agentic systems design.

---

## Architecture

Event Generator
↓
MinIO (lake-raw)
↓
Loader (JSONL → raw.raw_events)
↓
dbt staging (stg_events)
↓
dbt mart (fct_events_daily, incremental)
↓
Freshness Agent (detect → remediate → log)

---

### Components

- **MinIO** — S3-compatible object storage  
- **Postgres** — Data warehouse  
- **dbt** — Transformations, tests, documentation  
- **Python services** — Generator, loader, agent  
- **Docker Compose** — Local orchestration  
- **Makefile** — Developer experience shortcuts  

---

## Project Structure

- infra/ → Postgres + MinIO initialization
- services/
- generator/ → Event generation to MinIO
- loader/ → JSONL ingestion into Postgres
- dbt/ → Transformations, tests, docs
- agent/ → Freshness detection + remediation
- data/sample/ → Example data
- docker-compose.yml → Infrastructure definition
= Makefile → DX shortcuts

---

## Quickstart

### 1. Configure environment

```bash
cp .env.example .env
```
### Generate Event Data

```bash
docker compose --profile tools run --rm generator
```

---

### Load Latest Partition into Postgres

```bash
docker compose --profile tools run --rm \
  -e LOAD_KEY=events/dt=YYYY-MM-DD/events_YYYY-MM-DD.jsonl \
  loader

---

```
### 5. Run Transformations

```bash
cd services/dbt
dbt run
dbt test
```
Models created:
- dbt_staging.stg_events
- dbt_mart.fct_events_daily (incremental model)
Tests validate:
- Non-null fields
- Unique keys
- Source integrity
---

### Explore Lineage

```bash
dbt docs generate
dbt docs serve --port 8085 --no-browser
```
Open in your browser:
```bash
http://localhost:8085
```

---

## Data Model
### raw.raw_events

Raw ingested event stream from MinIO.

### stg_events

Typed and normalized staging model.

Fields include:

- `event_id`
- `event_ts`
- `device_type`
- `event_type`
- `revenue`

### fct_events_daily (incremental)

Aggregated daily metrics:

- `event_day`
- `device_type`
- `event_type`
- `event_count`
- `revenue`

## Agent Behavior

The agent simulates autonomous data pipeline operations.

It performs the following workflow:

1. Runs `dbt source freshness`
2. Detects stale sources
3. Generates a new event partition
4. Identifies the latest object in MinIO
5. Loads data into Postgres
6. Re-runs dbt transformations and tests
7. Logs execution metadata into `ops.agent_runs`

This models automated remediation logic commonly required in production systems.

## Observability

The system includes:

- dbt source freshness checks
- dbt data tests
- Agent execution logging
- Operational telemetry table (`ops.agent_runs`)

Example query:

```sql
SELECT run_id, created_at, status
FROM ops.agent_runs
ORDER BY run_id DESC;
```
---

## Design Decisions

- Local-first architecture for reproducibility  
- Object storage + warehouse separation  
- Incremental mart model for efficiency  
- Agent pattern for autonomous remediation  
- Fully containerized environment for portability

## Roadmap

Planned extensions:

- Great Expectations integration  
- Volume anomaly detection  
- Dagster orchestration  
- CI pipeline for dbt tests  
- Metrics layer / semantic modeling  
- Multi-partition auto-loading

## Why This Project

This repository demonstrates:

- End-to-end data pipeline design  
- Modern analytics engineering practices  
- Warehouse + object storage integration  
- Observability and freshness monitoring  
- Autonomous remediation patterns  

It bridges data engineering fundamentals with agentic system behavior.

