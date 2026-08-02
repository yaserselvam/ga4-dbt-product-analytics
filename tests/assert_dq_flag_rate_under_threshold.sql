-- Distribution monitor: warn if more than 2% of sessions carry a data-quality
-- flag. Configured as a WARNING, not an error: a data-quality spike must be
-- reviewed and alerted (the monitor picks warnings up and tags the owner), not
-- hard-block the build and not be silently dropped. Returns a row (test fails)
-- only when the threshold is breached.
{{ config(severity = 'warn') }}

with rate as (
    select avg(case when has_dq_flag then 1.0 else 0.0 end) as flag_rate
    from {{ ref('session_quality_flags') }}
)

select flag_rate
from rate
where flag_rate > 0.02
