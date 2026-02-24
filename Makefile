SHELL := /bin/bash

.DEFAULT_GOAL := help

help:
	@echo "Targets:"
	@echo "  make up        - Start core services (Postgres + MinIO)"
	@echo "  make down      - Stop services"
	@echo "  make ps        - Show running services"
	@echo "  make logs      - Tail logs"
	@echo "  make psql      - Open psql shell into Postgres container"
	@echo "  make minio     - Print MinIO console URL"
	@echo "  make buckets   - List MinIO buckets via mc (in container)"
	@echo "  make reset     - DANGEROUS: remove volumes and start fresh"

up:
	docker compose up -d

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f --tail=200

psql:
	docker exec -it adops-postgres psql -U $$POSTGRES_USER -d $$POSTGRES_DB

minio:
	@echo "MinIO API:     http://localhost:$$MINIO_PORT"
	@echo "MinIO Console: http://localhost:$$MINIO_CONSOLE_PORT"

buckets:
	docker run --rm --network agentic-dataops_default \
	  --entrypoint /bin/sh \
	  -e MINIO_ROOT_USER -e MINIO_ROOT_PASSWORD \
	  minio/mc:latest -c \
	  'mc alias set local http://minio:9000 "$$MINIO_ROOT_USER" "$$MINIO_ROOT_PASSWORD" >/dev/null && mc ls local'

reset:
	docker compose down -v
