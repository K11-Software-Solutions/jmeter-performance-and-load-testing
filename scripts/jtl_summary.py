#!/usr/bin/env python3
"""Summarise a JMeter CSV results file (.jtl) and optionally enforce pass/fail thresholds.

Standard library only, so it runs anywhere Python 3.8+ runs (including GitHub Actions).

Examples
  python scripts/jtl_summary.py results/smoke.jtl
  python scripts/jtl_summary.py results/smoke.jtl --p95-max 3000 --error-max 1.0
  python scripts/jtl_summary.py results/smoke.jtl --format markdown --out results/summary.md

What it reports per label (sampler or transaction) and for all requests:
  samples, errors, error %, average, min, max, p50, p90, p95, p99 (ms) and throughput (per second).

Notes
  * Transaction Controller samples (labels starting with "TX") are listed but left out of the
    "ALL REQUESTS" row, so requests are not counted twice.
  * Percentiles use the nearest-rank method. JMeter's HTML dashboard uses a slightly different
    formula, so the two can differ by a few milliseconds. That is normal.
  * Exit code is 1 when a threshold is breached, 2 when the file is missing or empty.
"""
import argparse
import csv
import math
import re
import sys
from collections import defaultdict


def percentile(sorted_values, pct):
    if not sorted_values:
        return 0
    rank = max(1, math.ceil(pct / 100.0 * len(sorted_values)))
    return sorted_values[rank - 1]


def stats(rows):
    elapsed = sorted(int(r["elapsed"]) for r in rows)
    errors = sum(1 for r in rows if r["success"].lower() != "true")
    start = min(int(r["timeStamp"]) for r in rows)
    end = max(int(r["timeStamp"]) + int(r["elapsed"]) for r in rows)
    seconds = max((end - start) / 1000.0, 0.001)
    return {
        "samples": len(rows),
        "errors": errors,
        "error_pct": 100.0 * errors / len(rows),
        "avg": sum(elapsed) / len(elapsed),
        "min": elapsed[0],
        "max": elapsed[-1],
        "p50": percentile(elapsed, 50),
        "p90": percentile(elapsed, 90),
        "p95": percentile(elapsed, 95),
        "p99": percentile(elapsed, 99),
        "throughput": len(rows) / seconds,
    }


COLUMNS = [("samples", "Samples", "{:d}"), ("errors", "Errors", "{:d}"), ("error_pct", "Error %", "{:.2f}"),
           ("avg", "Avg ms", "{:.0f}"), ("min", "Min ms", "{:d}"), ("max", "Max ms", "{:d}"),
           ("p50", "p50 ms", "{:d}"), ("p90", "p90 ms", "{:d}"), ("p95", "p95 ms", "{:d}"),
           ("p99", "p99 ms", "{:d}"), ("throughput", "Throughput/s", "{:.2f}")]


def render(table, fmt):
    header = ["Label"] + [c[1] for c in COLUMNS]
    lines = []
    body = [[label] + [c[2].format(s[c[0]]) for c in COLUMNS] for label, s in table]
    if fmt == "markdown":
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join(["---"] + ["---:"] * len(COLUMNS)) + "|")
        lines += ["| " + " | ".join(row) + " |" for row in body]
    elif fmt == "csv":
        lines.append(",".join(header))
        lines += [",".join('"' + v + '"' if "," in v else v for v in row) for row in body]
    else:
        widths = [max(len(str(x)) for x in col) for col in zip(header, *body)]
        fmt_row = lambda row: "  ".join(str(v).ljust(w) if i == 0 else str(v).rjust(w) for i, (v, w) in enumerate(zip(row, widths)))
        lines.append(fmt_row(header))
        lines.append("  ".join("-" * w for w in widths))
        lines += [fmt_row(row) for row in body]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("jtl", help="JMeter results file in CSV format")
    ap.add_argument("--format", choices=["text", "markdown", "csv"], default="text")
    ap.add_argument("--out", help="also write the table to this file")
    ap.add_argument("--include", help="only labels matching this regular expression")
    ap.add_argument("--p95-max", type=float, help="fail if ALL REQUESTS p95 is above this (ms)")
    ap.add_argument("--p95-max-label", action="append", default=[], metavar="REGEX=MS",
                    help="fail if any label matching REGEX has p95 above MS (repeatable)")
    ap.add_argument("--error-max", type=float, help="fail if ALL REQUESTS error %% is above this")
    ap.add_argument("--fail-on-errors", action="store_true", help="fail if any sample failed")
    a = ap.parse_args()

    try:
        with open(a.jtl, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        print("Results file not found: " + a.jtl, file=sys.stderr)
        return 2
    if a.include:
        rx = re.compile(a.include)
        rows = [r for r in rows if rx.search(r["label"])]
    if not rows:
        print("No samples found in " + a.jtl, file=sys.stderr)
        return 2

    by_label = defaultdict(list)
    for r in rows:
        by_label[r["label"]].append(r)
    requests = [r for r in rows if not r["label"].startswith("TX")]

    table = [(label, stats(rs)) for label, rs in sorted(by_label.items())]
    overall = stats(requests) if requests else stats(rows)
    table.append(("ALL REQUESTS" if requests else "ALL TRANSACTIONS", overall))

    out = render(table, a.format)
    print(out)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(out + "\n")

    failures = []
    if a.p95_max is not None and overall["p95"] > a.p95_max:
        failures.append("p95 {} ms is above the {} ms limit".format(overall["p95"], a.p95_max))
    if a.error_max is not None and overall["error_pct"] > a.error_max:
        failures.append("error rate {:.2f}% is above the {}% limit".format(overall["error_pct"], a.error_max))
    for spec in a.p95_max_label:
        rx, ms = spec.rsplit("=", 1)
        for label, s in table:
            if not label.startswith("ALL ") and re.search(rx, label) and s["p95"] > float(ms):
                failures.append("{}: p95 {} ms is above the {} ms limit".format(label, s["p95"], ms))
    if a.fail_on_errors:
        for label, s in table:
            if not label.startswith("ALL ") and s["errors"]:
                failures.append("{}: {} failed sample(s)".format(label, s["errors"]))
        if not requests and overall["errors"]:
            failures.append("{} failed sample(s)".format(overall["errors"]))

    if failures:
        print("\nTHRESHOLDS FAILED:")
        for msg in failures:
            print("  - " + msg)
        return 1
    if a.p95_max is not None or a.error_max is not None or a.p95_max_label or a.fail_on_errors:
        print("\nAll thresholds passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
