SHELL := /bin/bash
.DEFAULT_GOAL := help

help:
	@echo "Targets:"
	@echo "  make up       - Start core services"
	@echo "  make down     - Stop services"
	@echo "  make ps       - Show running services"
	@echo "  make logs     - Tail logs"
	@echo "  make psql     - Open psql shell into Postgres container"
	@echo "  make minio    - Print MinIO console URL"
	@echo "  make buckets  - List MinIO buckets"
	@echo "  make generate - Generate one event partition in MinIO"
	@echo "  make load     - Load the latest generated partition into Postgres"
	@echo "  make dbt-run  - Run dbt models"
	@echo "  make dbt-test - Run dbt tests"
	@echo "  make agent    - Run freshness remediation agent"
	@echo "  make report   - Generate SVG report assets from warehouse data"
	@echo "  make dashboard - Start the Streamlit dashboard"
	@echo "  make dbt-docs-generate - Generate dbt documentation"
	@echo "  make dbt-docs-serve - Serve dbt documentation on localhost:8085"
	@echo "  make demo     - Run the local demo path"
	@echo "  make validate - Validate compose and dbt project configuration"
	@echo "  make reset    - Remove volumes and start fresh"

up:
	docker compose up -d

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f --tail=200

psql:
	docker exec -it adops-postgres sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

minio:
	@echo "MinIO API: http://localhost:$${MINIO_PORT:-9000}"
	@echo "MinIO Console: http://localhost:$${MINIO_CONSOLE_PORT:-9001}"

buckets:
	docker compose run --rm --entrypoint /bin/sh minio-init -c \
		'mc alias set local http://minio:9000 "$$MINIO_ROOT_USER" "$$MINIO_ROOT_PASSWORD" >/dev/null && mc ls local'

generate:
	docker compose --profile tools run --rm generator

load:
	@key=$$(docker compose run --rm --entrypoint /bin/sh minio-init -c 'mc alias set local http://minio:9000 "$$MINIO_ROOT_USER" "$$MINIO_ROOT_PASSWORD" >/dev/null && mc find local/lake-raw/events --name "*.jsonl" --maxdepth 6 | sort | tail -n 1 | sed "s#local/lake-raw/##"'); \
	if [ -z "$$key" ]; then echo "No event files found. Run make generate first."; exit 1; fi; \
	echo "Loading $$key"; \
	docker compose --profile tools run --rm -e LOAD_KEY="$$key" loader

dbt-run:
	docker compose --profile tools run --rm dbt dbt run

dbt-test:
	docker compose --profile tools run --rm dbt dbt test

agent:
	docker compose --profile tools run --rm agent

report:
	python3 scripts/generate_report.py

dashboard:
	docker compose --profile dashboard up --build dashboard

dbt-docs-generate:
	docker compose --profile tools run --rm dbt dbt docs generate

dbt-docs-serve:
	docker compose --profile tools run --rm -p 8085:8085 dbt dbt docs serve --host 0.0.0.0 --port 8085

demo: up generate load dbt-run dbt-test
	@echo "Demo complete. Run 'make agent' to exercise freshness remediation."

validate:
	docker compose config >/dev/null
	docker compose --profile tools run --rm dbt dbt parse

reset:
	docker compose down -v
