#!/usr/bin/env python3
"""Step (stress) test: run the Claims Summary workload at increasing user counts and build one table.

This is how you find the "knee": the load where throughput stops growing and response times climb.

1. Start the mock with a small connection pool so the knee appears at laptop-friendly load:
       POOL_SIZE=4 node mock-server/server.js            (Git Bash / macOS / Linux)
       $env:POOL_SIZE=4; node mock-server/server.js      (PowerShell)
2. Run:
       python scripts/step_load.py --users 10 20 40 80 --duration 90

For each step it runs test-plans/10_claims_summary_load.jmx with the stress profile, writes
results/step-load/users-<N>.jtl, reads the mock's /metrics endpoint (server-side view), and at the
end prints and saves results/step-load/step-summary.md and step-summary.csv.

JMeter is found from JMETER_HOME or from `jmeter` on the PATH.
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from jtl_summary import stats  # noqa: E402
from run_tutorials import jmeter_cmd  # noqa: E402
import csv  # noqa: E402


def read_metrics(base):
    try:
        with urllib.request.urlopen(base + "/metrics", timeout=5) as r:
            return json.load(r)
    except Exception:
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--users", nargs="+", type=int, default=[10, 20, 40, 80])
    ap.add_argument("--duration", type=int, default=90, help="seconds per step (after ramp-up starts)")
    ap.add_argument("--rampup", type=int, default=20)
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", default="3000")
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "step-load"))
    ap.add_argument("--html-for-last", action="store_true", help="also build the HTML dashboard for the last step")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    base = "http://{}:{}".format(a.host, a.port)
    jm = jmeter_cmd()
    rows = []
    for i, users in enumerate(a.users):
        jtl = os.path.join(a.out, "users-{}.jtl".format(users))
        if os.path.exists(jtl):
            os.remove(jtl)
        before = read_metrics(base)
        cmd = [jm, "-n", "-t", os.path.join(ROOT, "test-plans", "10_claims_summary_load.jmx"),
               "-q", os.path.join(ROOT, "test-plans", "profiles", "stress.properties"),
               "-q", os.path.join(ROOT, "test-plans", "report.properties"),
               "-Jusers={}".format(users), "-Jrampup={}".format(a.rampup), "-Jduration={}".format(a.duration),
               "-Jhost=" + a.host, "-Jport=" + a.port,
               "-l", jtl, "-j", os.path.join(a.out, "users-{}.log".format(users))]
        last = i == len(a.users) - 1
        if last and a.html_for_last:
            html = os.path.join(a.out, "html-users-{}".format(users))
            if os.path.exists(html):
                import shutil
                shutil.rmtree(html)
            cmd += ["-e", "-o", html]
        print("\n=== Step {}/{}: {} users".format(i + 1, len(a.users), users), flush=True)
        subprocess.call(cmd)
        after = read_metrics(base)
        with open(jtl, newline="", encoding="utf-8") as f:
            samples = [r for r in csv.DictReader(f) if not r["label"].startswith("TX")]
        s = stats(samples)
        rows.append({
            "users": users, "samples": s["samples"], "avg_ms": round(s["avg"]), "p90_ms": s["p90"],
            "p95_ms": s["p95"], "p99_ms": s["p99"], "throughput_per_s": round(s["throughput"], 1),
            "error_pct": round(s["error_pct"], 2),
            "ok_throughput_per_s": round(s["throughput"] * (1 - s["error_pct"] / 100.0), 1),
            "server_max_queue": after.get("maxQueueSeen", ""),
            "server_503s_this_step": (after.get("rejected503", 0) - before.get("rejected503", 0)) if after else "",
        })

    cols = list(rows[0].keys())
    with open(os.path.join(a.out, "step-summary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    md = ["| Users | Samples | Avg (ms) | p90 (ms) | p95 (ms) | p99 (ms) | Throughput (req/s) | Error % | Successful (req/s) | Server max queue | Server 503s |",
          "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        md.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    text = "\n".join(md)
    with open(os.path.join(a.out, "step-summary.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")
    print("\n" + text)
    print("\nNote: 'Server max queue' is the highest queue length seen since the mock started.")


if __name__ == "__main__":
    main()
