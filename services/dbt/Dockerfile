FROM python:3.11-slim

WORKDIR /workspace/services/dbt

RUN pip install --no-cache-dir dbt-core==1.11.2 dbt-postgres==1.8.2

ENV DBT_PROFILES_DIR=/workspace/services/dbt

CMD ["dbt", "--help"]
