-- Data-quality flags on sessions: FLAG anomalies, never DROP them.
--
-- Monzo's production principle (the CHECK_ZERO_PRICE pattern): a suspicious row
-- is marked for review, not silently discarded. Dropping "bad" rows hides the
-- data issue AND loses potentially real signal; flagging surfaces the issue to
-- the owning team while keeping every row auditable. Each rule below is a
-- tracking or integrity violation a data team would want alerted on, not deleted.

with sessions as (
    select * from {{ ref('fct_sessions') }}
),

flagged as (
    select
        session_key,
        session_date,
        revenue_usd,
        did_view_item,
        did_add_to_cart,
        did_begin_checkout,
        did_purchase,

        -- Funnel monotonicity: a later step is impossible without the earlier one.
        (did_purchase and not did_begin_checkout)            as flag_purchase_without_checkout,
        (did_add_to_cart and not did_view_item)              as flag_addcart_without_view,

        -- Revenue integrity. coalesce keeps these non-null: revenue_usd is a SUM
        -- over purchase events, which is NULL for the many sessions with no
        -- purchase, and a NULL flag would make has_dq_flag NULL downstream.
        (coalesce(revenue_usd, 0) > 0 and not did_purchase)  as flag_revenue_without_purchase,
        (coalesce(revenue_usd, 0) < 0)                       as flag_negative_revenue
    from sessions
)

select
    *,
    (
        case when flag_purchase_without_checkout then 1 else 0 end
      + case when flag_addcart_without_view      then 1 else 0 end
      + case when flag_revenue_without_purchase  then 1 else 0 end
      + case when flag_negative_revenue          then 1 else 0 end
    ) as dq_flag_count,
    (
        flag_purchase_without_checkout
        or flag_addcart_without_view
        or flag_revenue_without_purchase
        or flag_negative_revenue
    ) as has_dq_flag
from flagged
