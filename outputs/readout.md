# Readout: GA4 E-commerce Product Analytics

Built end to end on the public **GA4 obfuscated e-commerce** dataset in BigQuery, modelled with **dbt** (staging to marts, 15/15 tests passing), analysed for funnel, retention, and segmentation. All figures below come from the dbt marts.

**Headline recommendation: fix the product-page to add-to-cart step first.** It is by far the biggest leak in the funnel, a 1pp improvement there is worth more than optimising anything downstream.

---

## Funnel (`funnel.png`)

User-level purchase funnel over Nov 2020 to Jan 2021:

| Step | Users | % of viewers | Conversion from previous step |
|---|---|---|---|
| View item | 61,252 | 100% | - |
| Add to cart | 12,545 | 20.5% | **20.5%** |
| Begin checkout | 9,715 | 15.9% | 77.4% |
| Purchase | 4,419 | 7.2% | 45.5% |

**Interpretation:**
- **The dominant leak is view to add-to-cart: only 1 in 5 people who view a product add it.** This is where the volume and the opportunity are.
- **Cart to checkout is healthy (77%)** - once someone adds to cart, they mostly proceed. Not a priority.
- **Checkout to purchase loses over half (45.5%)** - a real secondary problem (likely payment friction, unexpected shipping cost, or forced account creation).
- Overall view-to-purchase is 7.2%.

**What I'd do:** prioritise the product page and add-to-cart experience (merchandising, price clarity, a stronger CTA), then reduce checkout abandonment. I would A/B test each change rather than assume, tying back to the separate experimentation project.

## Retention (`retention_cohorts.png`)

Weekly acquisition cohorts by weeks-since-first-visit, as a % of each cohort's week-0 users. As expected for transactional e-commerce, weekly return rates fall off sharply after week 0, the value is in the first-purchase window, which reinforces converting the funnel over chasing weekly repeat visits.

## Segments (`segments.png`)

RFM scoring of the 4,419 purchasing users into six named segments:

| Segment | Users | Avg revenue (USD) |
|---|---|---|
| Loyal | 1,020 | ~105 |
| Needs Attention | 872 | ~65 |
| Hibernating | 750 | ~81 |
| Champions | 747 | ~90 |
| New / Promising | 672 | ~58 |
| At Risk | 358 | ~86 |

**Use:** protect Champions and Loyal (highest value, retention not acquisition); nurture New / Promising into repeat buyers; run win-back on At Risk and Hibernating, who still carry meaningful average value.

---

## Method note

- **Modern stack, shipped:** GA4 raw events -> dbt (`stg` view -> `fct_sessions` -> funnel / retention / RFM marts) on BigQuery, with sources, tests (not-null, unique, accepted-values) and docs. `dbt build` = PASS 15/15.
- **Trustworthy by construction:** validity is enforced by tests, not assumed; the funnel counts are monotonic (view >= cart >= checkout >= purchase) as a sanity check.
- **Verified by hand:** every statistical and modelling choice was checked against the raw events before being trusted, not assumed from a first pass.
- **Reproducible:** anyone with a BigQuery sandbox can `dbt build` this from the public dataset and get the same tables.
