-- Volume monitor: the funnel/retention/RFM marts are only trustworthy if the
-- session table is roughly the size we expect. The full public GA4 sample
-- produces ~360k sessions; a build landing far outside that band signals a
-- broken source load or a partial run, so it should alert rather than pass
-- silently. Returns a row (test fails) when volume is out of band.
--
-- On live data this is where you would switch to a time-series volume-anomaly
-- test (see observability/README.md); on a static public dataset a fixed band
-- is the honest, reproducible equivalent.
{{ config(severity = 'warn') }}

with volume as (
    select count(*) as session_count
    from {{ ref('fct_sessions') }}
)

select session_count
from volume
where session_count < 300000
   or session_count > 420000
