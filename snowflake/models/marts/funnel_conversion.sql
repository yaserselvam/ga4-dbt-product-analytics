-- User-level purchase funnel in long (chart-friendly) format.
-- Snowflake dialect: countif -> count_if, logical_or -> boolor_agg,
-- safe_divide(a,b) -> iff(b = 0, null, a / b).

with per_user as (
    select
        user_pseudo_id,
        boolor_agg(did_view_item)      as viewed_item,
        boolor_agg(did_add_to_cart)    as added_to_cart,
        boolor_agg(did_begin_checkout) as began_checkout,
        boolor_agg(did_purchase)       as purchased
    from {{ ref('fct_sessions') }}
    group by 1
),

agg as (
    select
        count_if(viewed_item)     as s1,
        count_if(added_to_cart)   as s2,
        count_if(began_checkout)  as s3,
        count_if(purchased)       as s4
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
    round(iff(max(users) over () = 0, null,
              users / max(users) over ()) * 100, 1)                             as pct_of_top,
    round(iff(lag(users) over (order by step_order) = 0, null,
              users / lag(users) over (order by step_order)) * 100, 1)          as pct_of_previous_step
from funnel
order by step_order
