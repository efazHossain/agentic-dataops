# Agentic DataOps Platform

A local-first analytics engineering and DataOps platform that simulates an end-to-end event data pipeline using Docker, MinIO, PostgreSQL, dbt, and Python-based monitoring services.

This project demonstrates practical data engineering skills across ingestion, object storage, warehouse loading, transformation, data quality checks, freshness monitoring, and operational remediation workflows.

## Project Overview

Modern analytics systems need more than data movement. They need reliable ingestion, tested transformations, monitoring, and clear operational workflows.

This project builds a local DataOps environment that:

- Generates synthetic event data
- Stores raw files in MinIO object storage
- Loads event data into PostgreSQL
- Transforms warehouse tables using dbt
- Runs data quality and freshness checks
- Uses a Python agent service to monitor pipeline health and log remediation activity
- Provides reproducible local development through Docker Compose and Makefile commands

The goal is to simulate how a small production-style analytics platform could be structured for local development, testing, and portfolio demonstration.

## Architecture

```mermaid
flowchart LR
    A[Event Generator] --> B[MinIO Raw Lake]
    B --> C[Loader Service]
    C --> D[PostgreSQL Warehouse]
    D --> E[dbt Staging Models]
    E --> F[dbt Mart Models]
    F --> G[dbt Tests + Data Quality Checks]
    G --> H[Agent Monitor]
    H --> I[Freshness Checks + Remediation Logs]
```

## Tech Stack

| Category | Tools |
|---|---|
| Programming | Python, SQL |
| Containers | Docker, Docker Compose |
| Object Storage | MinIO |
| Warehouse | PostgreSQL |
| Transformation | dbt |
| Monitoring | Python agent service |
| Data Quality | dbt tests, freshness checks |
| DevOps | Makefile, environment configuration |

## Core Features

| Feature | Description |
|---|---|
| Synthetic event generation | Creates sample event data for pipeline testing |
| Object storage layer | Stores raw generated data in MinIO buckets |
| Warehouse loading | Loads raw event data into PostgreSQL |
| dbt transformations | Builds staging and mart models for analytics-ready tables |
| Data quality checks | Uses dbt tests to validate transformed data |
| Freshness monitoring | Detects stale or missing pipeline outputs |
| Agent-based remediation | Logs operational status and supports automated recovery patterns |
| Local reproducibility | Runs through Docker Compose and Makefile commands |

## Project Structure

```text
agentic-dataops/
│
├── data/
│   └── sample/
│
├── docs/
│   └── runbook.md
│
├── infra/
│   ├── minio/
│   └── postgres/
│
├── services/
│   ├── agent/
│   ├── dbt/
│   ├── generator/
│   └── loader/
│
├── docker-compose.yml
├── Makefile
├── requirements.txt
├── .env.example
└── README.md
```

## Quickstart

### 1. Clone the repository

```bash
git clone https://github.com/efazHossain/agentic-dataops.git
cd agentic-dataops
```

### 2. Create an environment file

```bash
cp .env.example .env
```

### 3. Start core services

```bash
make up
```

This starts the local infrastructure, including PostgreSQL, MinIO, and the MinIO initialization service.

### 4. Check running containers

```bash
make ps
```

### 5. View logs

```bash
make logs
```

### 6. Open PostgreSQL

```bash
make psql
```

### 7. View MinIO connection info

```bash
make minio
```

## Typical Workflow

Run the local pipeline in this order:

```bash
make up

docker compose --profile tools run --rm generator

LOAD_DATE=$(date -u +%F)
LOAD_KEY="events/dt=${LOAD_DATE}/events_${LOAD_DATE}.jsonl"

docker compose --profile tools run --rm \
  -e LOAD_KEY="$LOAD_KEY" \
  loader

cd services/dbt
dbt build
cd ../..

docker compose --profile tools run --rm agent
```

The loader requires a `LOAD_KEY` because the generated event file is stored in MinIO using a dated path such as:

```text
events/dt=2026-04-29/events_2026-04-29.jsonl
```

Using `date -u +%F` keeps the loader date aligned with the container-generated UTC date.

## dbt Transformation Layer

The dbt project is located in:

```text
services/dbt/
```

The dbt layer turns raw warehouse tables into analytics-ready models.

| Layer | Purpose |
|---|---|
| Source | Defines raw warehouse tables |
| Staging | Cleans and standardizes raw event data |
| Mart | Builds reporting-ready fact tables |
| Tests | Validates uniqueness, nulls, accepted values, and relationships |

## Validation Result

The dbt transformation layer was successfully validated locally.

```text
Finished running 1 incremental model, 8 data tests, 1 view model in 5.51 seconds.

Completed successfully

PASS=10 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=10
```

This confirms that the pipeline can build the staging view, incremental mart model, and dbt data tests successfully.

## Agent Monitoring Layer

The agent service monitors pipeline health and operational metadata.

The agent is designed to support:

- Freshness checks
- dbt status inspection
- Stale pipeline detection
- Remediation logging
- Operational observability

This gives the project a stronger DataOps focus beyond a basic ETL pipeline.

## Runbook

Operational instructions are documented in:

```text
docs/runbook.md
```

The runbook covers:

- Starting services
- Checking containers
- Generating event data
- Loading events into PostgreSQL
- Running dbt models
- Running the agent
- Common troubleshooting steps

## Environment Variables

A sample environment file is provided in:

```text
.env.example
```

Example variables include:

```text
POSTGRES_USER=agentic
POSTGRES_PASSWORD=agentic_pw
POSTGRES_DB=warehouse
POSTGRES_PORT=5432

MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001
MINIO_BUCKETS="lake-raw lake-logs lake-artifacts"
```

Do not commit your real `.env` file.

## Validation Commands

Use these commands to validate the local setup:

```bash
docker compose config
make help
make up
make ps
make buckets
```

Run dbt validation:

```bash
cd services/dbt
dbt build
cd ../..
```

## Why This Project Matters

This project demonstrates practical data engineering and analytics engineering skills, including:

- Building containerized data infrastructure
- Designing object storage and warehouse layers
- Writing SQL transformations with dbt
- Implementing data quality checks
- Creating reproducible local workflows
- Thinking operationally about freshness, failures, and remediation

It is intended to show not just that data can be moved, but that pipelines can be monitored, tested, and maintained.

## Future Improvements

- Add GitHub Actions for dbt validation
- Add Great Expectations checks for raw data validation
- Add Dagster or Airflow orchestration
- Add a lightweight dashboard for pipeline health metrics
- Add lineage documentation for dbt models
- Add alerting simulation for freshness failures
- Add more realistic event schemas and partitioned data layouts
