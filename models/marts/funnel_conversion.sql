-- User-level purchase funnel in long (chart-friendly) format:
-- one row per step with users reaching it, share of the top step, and
-- step-over-step conversion. Feeds the funnel view in Power BI.

with per_user as (
    select
        user_pseudo_id,
        logical_or(did_view_item)      as viewed_item,
        logical_or(did_add_to_cart)    as added_to_cart,
        logical_or(did_begin_checkout) as began_checkout,
        logical_or(did_purchase)       as purchased
    from {{ ref('fct_sessions') }}
    group by 1
),

agg as (
    select
        countif(viewed_item)     as s1,
        countif(added_to_cart)   as s2,
        countif(began_checkout)  as s3,
        countif(purchased)       as s4
    from per_user
),

funnel as (
    select 1 as step_order, 'View item'      as step, s1 as users from agg
    union all select 2, 'Add to cart',    s2 from agg
    union all select 3, 'Begin checkout', s3 from agg
    union all select 4, 'Purchase',       s4 from agg
)

select
    step_order,
    step,
    users,
    round(safe_divide(users, max(users) over ()) * 100, 1)                             as pct_of_top,
    round(safe_divide(users, lag(users) over (order by step_order)) * 100, 1)          as pct_of_previous_step
from funnel
order by step_order
