-- Session grain: one row per (user, session) with conversion flags and revenue.
-- The funnel/retention/RFM marts all build on this.

with events as (
    select * from {{ ref('stg_ga4__events') }}
)

select
    user_pseudo_id,
    ga_session_id,
    concat(user_pseudo_id, '-', cast(ga_session_id as string)) as session_key,

    min(event_ts)                                   as session_start,
    max(event_ts)                                   as session_end,
    min(event_date)                                 as session_date,

    any_value(device_category)                      as device_category,
    any_value(country)                              as country,
    any_value(traffic_medium)                       as traffic_medium,

    countif(event_name = 'page_view')               as page_views,
    countif(event_name = 'view_item')               as view_item_events,

    logical_or(event_name = 'view_item')            as did_view_item,
    logical_or(event_name = 'add_to_cart')          as did_add_to_cart,
    logical_or(event_name = 'begin_checkout')       as did_begin_checkout,
    logical_or(event_name = 'purchase')             as did_purchase,

    sum(purchase_revenue_usd)                       as revenue_usd
from events
group by 1, 2, 3
