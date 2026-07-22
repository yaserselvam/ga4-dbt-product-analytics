# Power BI dashboard

Connect Power BI to the dbt marts in your BigQuery project and build three views. The marts are small pre-aggregated tables, so **Import** mode is fine and fast.

## Connect

1. Power BI Desktop -> **Home -> Get Data -> More -> Database -> Google BigQuery**.
2. Sign in with the Google account that owns your sandbox project.
3. Navigate: your project -> `ga4_analytics` dataset -> select `funnel_conversion`, `retention_cohorts`, `rfm_segments` (and `fct_sessions` if you want session-level slicing).
4. **Import**. (These are aggregates, well under the free-tier limits.)

## Page 1 - Funnel

- **Visual:** funnel (or a sorted bar) from `funnel_conversion`: axis = `step` sorted by `step_order`, value = `users`.
- **Labels:** show `pct_of_previous_step` so the drop-off at each stage is obvious.
- **KPI card:** overall view-to-purchase conversion (the `pct_of_top` on the Purchase row).
- **Takeaway to write on the page:** the single biggest leak in the funnel and what you'd test to fix it.

## Page 2 - Retention cohorts (heatmap)

- **Visual:** Matrix. Rows = `cohort_week`, Columns = `weeks_since`, Values = a **Retention %** measure.
- **Retention % measure (DAX):**
  ```DAX
  Cohort Size =
  CALCULATE(
      SUM(retention_cohorts[active_users]),
      FILTER(ALLEXCEPT(retention_cohorts, retention_cohorts[cohort_week]),
             retention_cohorts[weeks_since] = 0)
  )

  Retention % =
  DIVIDE(SUM(retention_cohorts[active_users]), [Cohort Size])
  ```
- **Conditional formatting:** colour scale on `Retention %` to make it a heatmap.
- **Takeaway:** which cohorts retain best, and where the steepest week-1 drop is.

## Page 3 - RFM segments

- **Bar:** users by `segment` from `rfm_segments`.
- **Scatter:** `recency_days` (x) vs `frequency` (y), bubble size = `monetary_usd`, colour = `segment`.
- **Table:** `segment`, count of users, avg `monetary_usd`, avg `frequency`.
- **Takeaway:** which segments to protect (Champions), grow (Loyal/New), or win back (At Risk).

## Note on the Power BI gap

This is deliberately the piece that closes the hands-on Power BI depth gap: a governed BigQuery source, DAX measures (Cohort Size / Retention %), and three decision-oriented pages, not just a chart dump. Export the pages as PNGs into `../outputs/` and reference them from the top-level README.
