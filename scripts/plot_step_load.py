#!/usr/bin/env python3
"""Draw the step (stress) test chart: throughput and response time against users.

    pip install matplotlib
    python scripts/plot_step_load.py results/step-load/step-summary.csv docs/images/step-load-chart.png
"""
import csv
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

NAVY, BLUE, LIGHT, RED = "#1F2749", "#008ADD", "#7CC8F5", "#C0392B"


def main(src, dst):
    with open(src, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    users = [int(r["users"]) for r in rows]
    labels = [str(u) for u in users]
    tput = [float(r["throughput_per_s"]) for r in rows]
    ok = [float(r.get("ok_throughput_per_s") or r["throughput_per_s"]) for r in rows]
    failed = [t - o for t, o in zip(tput, ok)]
    avg = [float(r["avg_ms"]) / 1000 for r in rows]
    p95 = [float(r["p95_ms"]) / 1000 for r in rows]
    err = [float(r["error_pct"]) for r in rows]

    plt.rcParams.update({"font.family": "Segoe UI", "font.size": 10})
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2), dpi=160)

    x = range(len(users))
    ax1.bar(x, ok, color=BLUE, width=0.6, label="successful")
    ax1.bar(x, failed, bottom=ok, color=RED, alpha=0.75, width=0.6, label="failed (503)")
    for i, (o, f) in enumerate(zip(ok, failed)):
        ax1.text(i, o / 2, "%.1f" % o, ha="center", va="center", color="white", fontsize=9, fontweight="bold")
        if f > 0.05:
            ax1.text(i, o + f + max(tput) * 0.02, "+%.1f failed" % f, ha="center", color=RED, fontsize=8.5)
    ax1.legend(frameon=False, loc="upper left")
    ax1.set_xticks(list(x), labels)
    ax1.set_xlabel("Concurrent users")
    ax1.set_ylabel("Throughput (requests per second)")
    ax1.set_title("Successful throughput stops growing", color=NAVY, fontweight="bold", loc="left")
    ax1.set_ylim(0, max(tput) * 1.2)

    ax2.plot(list(x), p95, marker="o", color=NAVY, linewidth=2.2, label="p95")
    ax2.plot(list(x), avg, marker="o", color=BLUE, linewidth=2.2, label="average")
    for i, v in enumerate(p95):
        ax2.annotate("%.2f s" % v, (i, v), textcoords="offset points", xytext=(0, 9), ha="center", fontsize=9, color=NAVY)
    notes = ["%d users: %.1f%% errors" % (u, e) for u, e in zip(users, err) if e > 0]
    if notes:
        ax2.text(0.02, 0.70, "\n".join(notes), transform=ax2.transAxes, fontsize=9, color=RED, fontweight="bold", va="top")
    ax2.set_xlim(-0.4, len(users) - 0.6)
    ax2.set_xticks(list(x), labels)
    ax2.set_xlabel("Concurrent users")
    ax2.set_ylabel("Response time (seconds)")
    ax2.set_title("...while response time climbs", color=NAVY, fontweight="bold", loc="left")
    ax2.set_ylim(0, max(p95) * 1.25)
    ax2.legend(frameon=False, loc="upper left")

    for ax in (ax1, ax2):
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#e3e8ef", linewidth=0.8)
        ax.set_axisbelow(True)

    fig.text(0.01, 0.01, "Step test of the local mock API (POOL_SIZE=4, QUEUE_TIMEOUT_MS=2000), JMeter 5.6.3, 90 s per step. "
             "Lab data for learning, not a benchmark.", fontsize=8, color="#6b7280")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(dst, facecolor="white")
    print("wrote", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
