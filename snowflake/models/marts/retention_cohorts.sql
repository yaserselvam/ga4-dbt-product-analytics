-- Weekly acquisition-cohort retention. Snowflake dialect: Monday-start weeks are
-- computed explicitly with dayofweekiso (deterministic, independent of WEEK_START),
-- and weeks_since = day difference / 7 (both dates are Monday-aligned).

with sessions as (
    select user_pseudo_id, session_date
    from {{ ref('fct_sessions') }}
),

first_seen as (
    select
        user_pseudo_id,
        dateadd(day, 1 - dayofweekiso(min(session_date)), min(session_date)) as cohort_week
    from sessions
    group by 1
),

activity as (
    select distinct
        user_pseudo_id,
        dateadd(day, 1 - dayofweekiso(session_date), session_date) as active_week
    from sessions
),

cohort as (
    select
        f.cohort_week,
        datediff(day, f.cohort_week, a.active_week) / 7 as weeks_since,
        a.user_pseudo_id
    from activity a
    join first_seen f using (user_pseudo_id)
)

select
    cohort_week,
    weeks_since,
    count(distinct user_pseudo_id) as active_users
from cohort
where weeks_since between 0 and 8
group by 1, 2
order by 1, 2
