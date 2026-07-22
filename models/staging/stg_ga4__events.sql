-- Flattens the nested GA4 export into one clean, typed row per event.
-- Pulls the event_params we actually use, and the top-level device/geo/traffic
-- and ecommerce fields. The _TABLE_SUFFIX bound keeps the scan (and cost) small.

with source as (
    select *
    from {{ source('ga4', 'events') }}
    -- sample spans 2020-11-01 to 2021-01-31; widen/narrow to trade coverage vs cost
    where _table_suffix between '20201101' and '20210131'
)

select
    -- identifiers
    user_pseudo_id,
    (select ep.value.int_value
       from unnest(event_params) ep
      where ep.key = 'ga_session_id')                       as ga_session_id,

    -- event
    event_name,
    timestamp_micros(event_timestamp)                       as event_ts,
    parse_date('%Y%m%d', event_date)                        as event_date,

    -- page / context
    (select ep.value.string_value
       from unnest(event_params) ep
      where ep.key = 'page_location')                       as page_location,
    device.category                                         as device_category,
    geo.country                                             as country,
    traffic_source.medium                                   as traffic_medium,
    traffic_source.source                                   as traffic_source,

    -- ecommerce value (present on purchase events in the sample; null otherwise)
    ecommerce.purchase_revenue_in_usd                       as purchase_revenue_usd

from source
-- guard against rare rows with no session id (cannot be attributed to a session)
where (select ep.value.int_value from unnest(event_params) ep where ep.key = 'ga_session_id') is not null
