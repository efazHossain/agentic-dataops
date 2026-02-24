import os
import boto3
from botocore.config import Config

def _s3_client():
    endpoint = os.getenv("S3_ENDPOINT", "http://minio:9000")
    access_key = os.getenv("MINIO_ROOT_USER")
    secret_key = os.getenv("MINIO_ROOT_PASSWORD")
    region = os.getenv("S3_REGION", "us-east-1")

    if not access_key or not secret_key:
        raise RuntimeError("Missing MINIO_ROOT_USER / MINIO_ROOT_PASSWORD in environment")

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        config=Config(signature_version="s3v4"),
    )

def write_jsonl_to_minio(bucket: str, key: str, data: bytes) -> None:
    s3 = _s3_client()
    s3.put_object(Bucket=bucket, Key=key, Body=data, ContentType="application/json")
