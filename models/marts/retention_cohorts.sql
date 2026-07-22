-- Weekly acquisition-cohort retention: for each cohort (week of first visit),
-- how many users are active N weeks later. Feeds the retention heatmap in Power BI.

with sessions as (
    select user_pseudo_id, session_date
    from {{ ref('fct_sessions') }}
),

first_seen as (
    select
        user_pseudo_id,
        date_trunc(min(session_date), week(monday)) as cohort_week
    from sessions
    group by 1
),

activity as (
    select distinct
        user_pseudo_id,
        date_trunc(session_date, week(monday)) as active_week
    from sessions
),

cohort as (
    select
        f.cohort_week,
        date_diff(a.active_week, f.cohort_week, week) as weeks_since,
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
