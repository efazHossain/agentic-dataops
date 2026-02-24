{{ config(
    materialized='incremental',
    unique_key=['event_day', 'device_type', 'event_type']
) }}

WITH base AS (
  SELECT
    event_day,
    device_type,
    event_type,
    COUNT(*) AS event_count,
    SUM(
      CASE
        WHEN event_type = 'purchase' THEN COALESCE(price, 0)
        ELSE 0
      END
    ) AS revenue
  FROM {{ ref('stg_events') }}
  {% if is_incremental() %}
    WHERE event_day >= (SELECT max(event_day) FROM {{ this }})
  {% endif %}
  GROUP BY 1, 2, 3
)

SELECT *
FROM base
