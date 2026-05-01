import os

import pandas as pd
import psycopg2
import streamlit as st


st.set_page_config(page_title="Agentic DataOps Dashboard", layout="wide")


def pg_conn():
    return psycopg2.connect(
        host=os.getenv("PGHOST", "postgres"),
        port=int(os.getenv("PGPORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "warehouse"),
        user=os.getenv("POSTGRES_USER", "agentic"),
        password=os.getenv("POSTGRES_PASSWORD", "agentic_pw"),
    )


@st.cache_data(ttl=30)
def query(sql: str) -> pd.DataFrame:
    with pg_conn() as conn:
        return pd.read_sql_query(sql, conn)


st.title("Agentic DataOps Dashboard")
st.caption("Warehouse metrics and freshness-agent telemetry from the local Docker Compose stack.")

summary = query(
    """
    SELECT COUNT(*) AS total_events,
           COUNT(DISTINCT user_id) AS unique_users,
           COUNT(*) FILTER (WHERE event_type = 'purchase') AS purchase_events,
           COALESCE(SUM(price) FILTER (WHERE event_type = 'purchase'), 0) AS purchase_revenue,
           MIN(event_ts)::date AS first_event_date,
           MAX(event_ts)::date AS latest_event_date
    FROM raw.raw_events;
    """
).iloc[0]

latest_run = query(
    """
    SELECT run_id, pipeline_name, status, started_at, ended_at
    FROM ops.pipeline_runs
    ORDER BY started_at DESC
    LIMIT 1;
    """
)

metric_cols = st.columns(4)
metric_cols[0].metric("Events", f"{int(summary.total_events):,}")
metric_cols[1].metric("Unique users", f"{int(summary.unique_users):,}")
metric_cols[2].metric("Purchases", f"{int(summary.purchase_events):,}")
metric_cols[3].metric("Revenue", f"${float(summary.purchase_revenue):,.2f}")

if not latest_run.empty:
    status = latest_run.iloc[0]["status"]
    st.info(f"Latest freshness agent run: {status} at {latest_run.iloc[0]['started_at']}")

left, right = st.columns(2)

with left:
    funnel = query(
        """
        SELECT event_type,
               COUNT(*) AS event_count
        FROM raw.raw_events
        GROUP BY event_type
        ORDER BY event_count DESC;
        """
    )
    st.subheader("Event Funnel")
    st.bar_chart(funnel.set_index("event_type"))

with right:
    device = query(
        """
        SELECT device_type,
               SUM(event_count) AS event_count,
               SUM(revenue) AS revenue
        FROM mart.fct_events_daily
        GROUP BY device_type
        ORDER BY event_count DESC;
        """
    )
    st.subheader("Revenue by Device")
    st.bar_chart(device.set_index("device_type")[["revenue"]])

daily = query(
    """
    SELECT event_day::date AS event_day,
           SUM(event_count) AS event_count
    FROM mart.fct_events_daily
    GROUP BY 1
    ORDER BY 1;
    """
)
st.subheader("Daily Event Volume")
st.line_chart(daily.set_index("event_day"))

st.subheader("Latest Mart Rows")
mart = query(
    """
    SELECT event_day::date AS event_day,
           device_type,
           event_type,
           event_count,
           revenue
    FROM mart.fct_events_daily
    ORDER BY event_day DESC, event_count DESC
    LIMIT 20;
    """
)
st.dataframe(mart, use_container_width=True, hide_index=True)

st.subheader("Agent Telemetry")
runs = query(
    """
    SELECT run_id, pipeline_name, status, started_at, ended_at
    FROM ops.pipeline_runs
    ORDER BY started_at DESC
    LIMIT 10;
    """
)
st.dataframe(runs, use_container_width=True, hide_index=True)
