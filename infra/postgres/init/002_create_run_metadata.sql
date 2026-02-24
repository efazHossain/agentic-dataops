CREATE TABLE IF NOT EXISTS ops.pipeline_runs (
  run_id        TEXT PRIMARY KEY,
  pipeline_name TEXT NOT NULL,
  status        TEXT NOT NULL CHECK (status IN ('SUCCESS','FAILED','RUNNING','DEGRADED')),
  started_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ended_at      TIMESTAMPTZ,
  error_message TEXT
);

CREATE TABLE IF NOT EXISTS ops.dq_results (
  id           BIGSERIAL PRIMARY KEY,
  run_id       TEXT NOT NULL REFERENCES ops.pipeline_runs(run_id) ON DELETE CASCADE,
  suite_name   TEXT NOT NULL,
  success      BOOLEAN NOT NULL,
  details_json JSONB,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops.agent_audit (
  id           BIGSERIAL PRIMARY KEY,
  run_id       TEXT,
  action_name  TEXT NOT NULL,
  input_json   JSONB,
  output_json  JSONB,
  success      BOOLEAN NOT NULL DEFAULT TRUE,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
