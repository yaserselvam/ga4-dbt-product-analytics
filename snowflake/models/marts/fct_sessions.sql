-- Session grain: one row per (user, session) with conversion flags and revenue.
-- Snowflake dialect: countif -> count_if, logical_or -> boolor_agg, concat/cast -> ||.

with events as (
    select * from {{ ref('stg_ga4__events') }}
)

select
    user_pseudo_id,
    ga_session_id,
    user_pseudo_id || '-' || ga_session_id::string  as session_key,

    min(event_ts)                               as session_start,
    max(event_ts)                               as session_end,
    min(event_date)                             as session_date,

    any_value(device_category)                  as device_category,
    any_value(country)                          as country,
    any_value(traffic_medium)                   as traffic_medium,

    count_if(event_name = 'page_view')          as page_views,
    count_if(event_name = 'view_item')          as view_item_events,

    boolor_agg(event_name = 'view_item')        as did_view_item,
    boolor_agg(event_name = 'add_to_cart')      as did_add_to_cart,
    boolor_agg(event_name = 'begin_checkout')   as did_begin_checkout,
    boolor_agg(event_name = 'purchase')         as did_purchase,

    sum(purchase_revenue_usd)                   as revenue_usd
from events
group by 1, 2, 3
