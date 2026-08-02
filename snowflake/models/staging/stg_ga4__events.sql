-- Snowflake staging: flatten the landed GA4 export into one clean, typed row per event.
-- BigQuery UNNEST(event_params) becomes LATERAL FLATTEN; the event_params element
-- shape is {key, value:{string_value, int_value, ...}}, same as the GA4 export.

with base as (
    select
        user_pseudo_id,
        event_name,
        event_timestamp,
        event_date,
        device:category::string          as device_category,
        geo:country::string              as country,
        traffic_source:medium::string    as traffic_medium,
        traffic_source:source::string    as traffic_source_name,
        ecommerce:purchase_revenue_in_usd::float as purchase_revenue_usd,
        event_params
    from {{ source('ga4_raw', 'events') }}
    -- sample spans 2020-11-01 to 2021-01-31; landing table is already scoped to it
),

-- pull the two params we use, one row per event, via conditional aggregation
params as (
    select
        user_pseudo_id,
        event_name,
        event_timestamp,
        event_date,
        device_category,
        country,
        traffic_medium,
        traffic_source_name,
        purchase_revenue_usd,
        max(case when p.value:key::string = 'ga_session_id'
                 then p.value:value:int_value::number end)    as ga_session_id,
        max(case when p.value:key::string = 'page_location'
                 then p.value:value:string_value::string end) as page_location
    from base,
         lateral flatten(input => base.event_params) p
    group by all
)

select
    user_pseudo_id,
    ga_session_id,
    event_name,
    to_timestamp_ntz(event_timestamp, 6)   as event_ts,
    to_date(event_date, 'YYYYMMDD')         as event_date,
    page_location,
    device_category,
    country,
    traffic_medium,
    traffic_source_name                     as traffic_source,
    purchase_revenue_usd
from params
-- guard against rare rows with no session id (cannot be attributed to a session)
where ga_session_id is not null
