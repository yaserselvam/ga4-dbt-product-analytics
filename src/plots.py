"""
Generate the readout figures from the dbt marts in BigQuery: funnel, RFM
segments, and a weekly cohort-retention heatmap. Saves PNGs to outputs/.

Auth: same service-account key dbt uses. Run from the project root:
    py src/plots.py
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from google.cloud import bigquery

KEY = r"C:/Users/YaserSe/keys/ga4-dbt-key.json"
PROJECT = "ga4-portfolio-503211"
DS = "ga4-portfolio-503211.ga4_analytics"
OUT = "outputs"
BLUE, LIGHT = "#2563eb", "#93c5fd"

os.makedirs(OUT, exist_ok=True)
client = bigquery.Client.from_service_account_json(KEY, project=PROJECT)


def funnel_chart():
    rows = list(client.query(
        f"select step, users, pct_of_top, pct_of_previous_step "
        f"from `{DS}.funnel_conversion` order by step_order"))
    steps = [r.step for r in rows]
    users = [r.users for r in rows]
    prev = [r.pct_of_previous_step for r in rows]
    fig, ax = plt.subplots(figsize=(7, 4.3))
    bars = ax.bar(steps, users, color=[BLUE, BLUE, LIGHT, LIGHT], width=0.6)
    for i, (b, u) in enumerate(zip(bars, users)):
        lbl = f"{u:,}"
        if prev[i] is not None:
            lbl += f"\n{prev[i]:.0f}% of prev"
        ax.text(b.get_x() + b.get_width() / 2, u + max(users) * 0.02, lbl,
                ha="center", va="bottom", fontsize=9)
    ax.set_title("Purchase funnel: biggest drop is view to add-to-cart (20.5%)", fontsize=11)
    ax.set_ylabel("Users")
    ax.set_ylim(0, max(users) * 1.18)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(f"{OUT}/funnel.png", dpi=150)
    print("wrote outputs/funnel.png")


def segments_chart():
    rows = list(client.query(
        f"select segment, count(*) users, round(avg(monetary_usd),0) avg_rev "
        f"from `{DS}.rfm_segments` group by segment order by users desc"))
    names = [r.segment for r in rows][::-1]
    users = [r.users for r in rows][::-1]
    avg = [r.avg_rev for r in rows][::-1]
    fig, ax = plt.subplots(figsize=(7, 4.3))
    bars = ax.barh(names, users, color=BLUE)
    for b, u, a in zip(bars, users, avg):
        ax.text(b.get_width() + max(users) * 0.01, b.get_y() + b.get_height() / 2,
                f"{u:,}  (~${a:.0f} avg)", va="center", fontsize=9)
    ax.set_title("RFM segments across 4,419 purchasers", fontsize=11)
    ax.set_xlabel("Users")
    ax.set_xlim(0, max(users) * 1.3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(f"{OUT}/segments.png", dpi=150)
    print("wrote outputs/segments.png")


def retention_chart():
    rows = list(client.query(
        f"select cast(cohort_week as string) cohort_week, weeks_since, active_users "
        f"from `{DS}.retention_cohorts` order by cohort_week, weeks_since"))
    data = defaultdict(dict)
    for r in rows:
        data[r.cohort_week][r.weeks_since] = r.active_users
    cohorts = sorted(data)
    maxw = max(r.weeks_since for r in rows)
    mat = np.full((len(cohorts), maxw + 1), np.nan)
    for i, ch in enumerate(cohorts):
        base = data[ch].get(0, 0)
        for w, u in data[ch].items():
            mat[i, w] = (u / base * 100) if base else np.nan
    fig, ax = plt.subplots(figsize=(8, 4.8))
    im = ax.imshow(mat, aspect="auto", cmap="Blues", vmin=0, vmax=100)
    ax.set_xticks(range(maxw + 1))
    ax.set_xticklabels([f"W{w}" for w in range(maxw + 1)])
    ax.set_yticks(range(len(cohorts)))
    ax.set_yticklabels(cohorts, fontsize=7)
    ax.set_title("Weekly cohort retention (% of each cohort's week-0 users)", fontsize=11)
    ax.set_xlabel("Weeks since first visit")
    ax.set_ylabel("Acquisition cohort")
    for i in range(len(cohorts)):
        for w in range(maxw + 1):
            if not np.isnan(mat[i, w]):
                ax.text(w, i, f"{mat[i, w]:.0f}", ha="center", va="center",
                        fontsize=6, color="white" if mat[i, w] > 50 else "#111827")
    fig.colorbar(im, label="retention %")
    fig.tight_layout()
    fig.savefig(f"{OUT}/retention_cohorts.png", dpi=150)
    print("wrote outputs/retention_cohorts.png")


if __name__ == "__main__":
    funnel_chart()
    segments_chart()
    retention_chart()
