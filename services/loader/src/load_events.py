import json
import os
import sys
from datetime import datetime

import boto3
import psycopg2
from psycopg2.extras import execute_values
from botocore.config import Config

def s3_client():
    endpoint = os.getenv("S3_ENDPOINT", "http://minio:9000")
    access_key = os.getenv("MINIO_ROOT_USER")
    secret_key = os.getenv("MINIO_ROOT_PASSWORD")
    if not access_key or not secret_key:
        raise RuntimeError("Missing MINIO_ROOT_USER / MINIO_ROOT_PASSWORD")
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=os.getenv("S3_REGION", "us-east-1"),
        config=Config(signature_version="s3v4"),
    )

def pg_conn():
    host = os.getenv("PGHOST", "postgres")
    port = int(os.getenv("PGPORT", "5432"))
    db = os.getenv("POSTGRES_DB", "warehouse")
    user = os.getenv("POSTGRES_USER", "agentic")
    pw = os.getenv("POSTGRES_PASSWORD", "agentic_pw")
    return psycopg2.connect(host=host, port=port, dbname=db, user=user, password=pw)

def main():
    bucket = os.getenv("LOAD_BUCKET", "lake-raw")
    key = os.getenv("LOAD_KEY")
    if not key:
        print("ERROR: LOAD_KEY is required (e.g., events/dt=2026-01-27/events_2026-01-27.jsonl)", file=sys.stderr)
        sys.exit(2)

    s3 = s3_client()
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = obj["Body"].read().decode("utf-8").splitlines()

    rows = []
    for line in data:
        if not line.strip():
            continue
        e = json.loads(line)
        rows.append((
            e.get("event_id"),
            e.get("user_id"),
            e.get("event_type"),
            e.get("event_ts"),
            e.get("device_type"),
            e.get("price"),
            e.get("currency"),
            e.get("source_version"),
            e.get("geo_country"),
            e.get("campaign_id"),
        ))

    if not rows:
        print("No rows found in object.")
        return

    insert_sql = """
    INSERT INTO raw.raw_events (
      event_id, user_id, event_type, event_ts, device_type,
      price, currency, source_version, geo_country, campaign_id
    ) VALUES %s
    ON CONFLICT (event_id) DO NOTHING
    """

    with pg_conn() as conn:
        with conn.cursor() as cur:
            execute_values(cur, insert_sql, rows, page_size=2000)
        conn.commit()

    print(f"Loaded {len(rows)} events from s3://{bucket}/{key} into raw.raw_events (deduped by event_id)")

if __name__ == "__main__":
    main()
