import os
import re
import subprocess
from datetime import datetime, timezone

import psycopg2

REPO_ROOT = os.getenv("REPO_ROOT", "/workspace")
DBT_DIR = os.getenv("DBT_PROJECT_DIR", "/workspace/services/dbt")

def run(cmd: list[str], cwd: str | None = None) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.returncode, p.stdout

def pg_conn():
    host = os.getenv("PGHOST", "postgres")
    port = int(os.getenv("PGPORT", "5432"))
    db = os.getenv("POSTGRES_DB", "warehouse")
    user = os.getenv("POSTGRES_USER", "agentic")
    pw = os.getenv("POSTGRES_PASSWORD", "agentic_pw")
    return psycopg2.connect(host=host, port=port, dbname=db, user=user, password=pw)

def log_run(status: str, details: str):
    with pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO ops.pipeline_runs (pipeline_name, status, details) VALUES (%s, %s, %s)",
                ("freshness_agent", status, details[:8000]),
            )
        conn.commit()

def minio_latest_key(prefix: str = "events/") -> str:
    # Configure mc alias using container env
    root_user = os.getenv("MINIO_ROOT_USER", "")
    root_pw = os.getenv("MINIO_ROOT_PASSWORD", "")
    if not root_user or not root_pw:
        raise RuntimeError("Missing MINIO_ROOT_USER/MINIO_ROOT_PASSWORD for MinIO access")

    # List objects in lake-raw/events and pick the latest by lexicographic sort (dt=YYYY-MM-DD works)
    cmd = [
        "sh", "-c",
        f'mc alias set local http://minio:9000 "{root_user}" "{root_pw}" >/dev/null && '
        f'mc find local/lake-raw/{prefix} --name "*.jsonl" --maxdepth 6 | sort | tail -n 1'
    ]
    code, out = run(cmd)
    key_line = out.strip().splitlines()[-1].strip() if out.strip() else ""
    if code != 0 or not key_line:
        raise RuntimeError(f"Failed to find latest jsonl key in MinIO. Output:\n{out}")

    # key_line looks like: local/lake-raw/events/dt=YYYY-MM-DD/file.jsonl
    # We want: events/dt=YYYY-MM-DD/file.jsonl
    m = re.search(r"local/lake-raw/(.+)$", key_line)
    if not m:
        raise RuntimeError(f"Unexpected mc find output: {key_line}")
    return m.group(1)

def run_loader(load_key: str) -> tuple[int, str]:
    # Runs loader container from the repo root (compose project)
    return run(
        ["docker", "compose", "--profile", "tools", "run", "--rm", "-e", f"LOAD_KEY={load_key}", "loader"],
        cwd=REPO_ROOT,
    )

def run_generator() -> tuple[int, str]:
    return run(["docker", "compose", "--profile", "tools", "run", "--rm", "generator"], cwd=REPO_ROOT)

def run_dbt() -> tuple[int, str, int, str]:
    r_code, r_out = run(["dbt", "run"], cwd=DBT_DIR)
    t_code, t_out = run(["dbt", "test"], cwd=DBT_DIR)
    return r_code, r_out, t_code, t_out

def run_freshness() -> tuple[int, str]:
    return run(["dbt", "source", "freshness"], cwd=DBT_DIR)

def main():
    started = datetime.now(timezone.utc).isoformat()

    f_code, f_out = run_freshness()
    if f_code == 0:
        msg = f"[{started}] freshness OK\n{f_out}"
        log_run("success", msg)
        print(msg)
        return

    stale = bool(re.search(r"ERROR\s+STALE|STALE freshness", f_out))
    if not stale:
        msg = f"[{started}] freshness failed (non-stale)\n{f_out}"
        log_run("error", msg)
        print(msg)
        raise SystemExit(f_code)

    # Remediation: generate -> find latest key -> load -> dbt run/test -> freshness again
    details = [f"[{started}] freshness=STALE -> remediate"]

    g_code, g_out = run_generator()
    details.append(f"generator_exit={g_code}")

    latest_key = minio_latest_key(prefix="events")
    details.append(f"latest_key={latest_key}")

    l_code, l_out = run_loader(latest_key)
    details.append(f"loader_exit={l_code}")

    r_code, r_out, t_code, t_out = run_dbt()
    details.append(f"dbt_run_exit={r_code}")
    details.append(f"dbt_test_exit={t_code}")

    f2_code, f2_out = run_freshness()
    details.append(f"freshness_after_exit={f2_code}")

    blob = (
        "\n".join(details)
        + "\n\n--- freshness(before) ---\n" + f_out
        + "\n\n--- generator ---\n" + g_out
        + "\n\n--- loader ---\n" + l_out
        + "\n\n--- dbt run ---\n" + r_out
        + "\n\n--- dbt test ---\n" + t_out
        + "\n\n--- freshness(after) ---\n" + f2_out
    )

    ok = (g_code == 0 and l_code == 0 and r_code == 0 and t_code == 0 and f2_code == 0)
    log_run("success" if ok else "error", blob)
    print(blob)

if __name__ == "__main__":
    main()
