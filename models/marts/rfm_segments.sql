-- RFM scoring + named segments for purchasing users.
-- Reference "today" is fixed at the day after the sample ends (data is historical),
-- so recency is deterministic and reproducible.

with purchases as (
    select
        user_pseudo_id,
        session_date,
        revenue_usd
    from {{ ref('fct_sessions') }}
    where did_purchase
      and revenue_usd is not null
),

user_rfm as (
    select
        user_pseudo_id,
        date_diff(date '2021-02-01', max(session_date), day) as recency_days,
        count(*)                                             as frequency,
        sum(revenue_usd)                                     as monetary_usd
    from purchases
    group by 1
),

scored as (
    select
        *,
        ntile(5) over (order by recency_days desc) as r_score,  -- most recent -> 5
        ntile(5) over (order by frequency asc)     as f_score,  -- most frequent -> 5
        ntile(5) over (order by monetary_usd asc)  as m_score   -- highest value -> 5
    from user_rfm
)

select
    *,
    case
        when r_score >= 4 and f_score >= 4 then 'Champions'
        when f_score >= 4                  then 'Loyal'
        when r_score >= 4 and f_score <= 2 then 'New / Promising'
        when r_score <= 2 and f_score >= 3 then 'At Risk'
        when r_score <= 2                  then 'Hibernating'
        else 'Needs Attention'
    end as segment
from scored
