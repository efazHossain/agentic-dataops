WITH src AS (
  SELECT *
  FROM {{ source('raw', 'raw_events') }}
)

SELECT
  event_id,
  user_id::bigint                          AS user_id,
  lower(event_type)                        AS event_type,
  event_ts::timestamptz                   AS event_ts,
  lower(device_type)                      AS device_type,
  price::numeric(10,2)                    AS price,
  currency,
  source_version,
  geo_country,
  campaign_id,
  ingested_at,
  date_trunc('day', event_ts)             AS event_day
FROM src
