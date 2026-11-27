# 10 · Non-GUI runs, profiles and the HTML dashboard

> **Goal:** run a real load test from the command line, switch between smoke, load, stress, spike and soak with property files, and generate JMeter's HTML dashboard report.
>
> **Script:** `test-plans/10_claims_summary_load.jmx` · **Profiles:** `test-plans/profiles/*.properties` · **Report settings:** `test-plans/report.properties`

## The workload model in plan 10

This is the Claims Summary load test, built against the local mock:

```
Test Plan: 10 Claims Summary load test        (every setting is a ${__P(...)} property)
├── Thread Group: Analysts (steady load)      users / rampup / duration
│   ├── HTTP Request Defaults, Header Manager
│   ├── CSV: users.csv (username, password, providerId)
│   ├── CSV: date_ranges.csv (from, to)
│   ├── TX01_Login → POST /api/auth/login → JSON Extractor: token
│   └── If: login worked (token found)
│       └── Loop: ACTIONS_PER_SESSION (default 4)
│           ├── Switch: weighted mix
│           │   ├── TX02_Dashboard        50%   GET /api/dashboard
│           │   ├── TX03_Claims_Summary   35%   GET /api/reports/claims-summary (assert totalPaid)
│           │   └── TX04_Export_Report    15%   report → If report worked: POST export
│           │                                   → poll until READY → If READY: download
│           └── Think time: Uniform Random Timer, THINK_MIN_MS + 0…THINK_RANGE_MS (3–8 s)
└── Thread Group: Spike burst                 0 users unless spike_users is set
```

**One iteration = one user session:** log in, then four actions with think time. Each session takes the next CSV row, so each session is a different analyst.

**The If Controllers are guards.** A real user whose login fails doesn't go on to open reports. Without the guards, one failed login turns into a string of 401 errors for the rest of the session, and one failed report into ten 404s from the poll loop. Those *cascade errors* hide the real problem in the results. Tutorial 14 shows the numbers from a run without the guards.

## The command line

```powershell
jmeter -n -t test-plans/10_claims_summary_load.jmx `
  -q test-plans/profiles/smoke.properties `
  -q test-plans/report.properties `
  -l results/smoke.jtl -j results/smoke.log `
  -e -o results/smoke-report
```

| Option | Meaning |
|---|---|
| `-n` | Non-GUI mode |
| `-t file.jmx` | Test plan |
| `-q file.properties` | Extra property file (you can pass several) |
| `-Jname=value` | Set one property, for example `-Jusers=50` (overrides `-q` files) |
| `-l results.jtl` | Results file |
| `-j jmeter.log` | Log file |
| `-e -o folder` | Generate the HTML dashboard after the test into an **empty or new** folder |
| `-f` | Delete an existing results file and report folder first |
| `-g results.jtl -o folder` | Generate the HTML report later from an existing results file (no test run) |
| `-G` / `-R` / `-X` | Distributed testing (Tutorial 11) |

This matches the command from the prep guide:

```
jmeter -n -t report_api_load.jmx -l results.jtl -e -o html-report -Jusers=200 -Jrampup=300 -Jduration=1800
```

## Profiles: one script, five test types

| Profile | Users | Ramp-up | Duration | Think time | Purpose |
|---|---|---|---|---|---|
| `smoke.properties` | 5 | 10 s | 60 s | 1–3 s | After each deploy, and in CI |
| `load.properties` | 300 | 600 s | 3600 s | 3–8 s | The target peak from the workload model |
| `stress.properties` | 50 per step | 30 s | 120 s | 0.5–1.5 s | Used by `scripts/step_load.py` to find the breaking point |
| `spike.properties` | 10 + 60 burst at 60 s | 10 s / 5 s | 240 s | 1–3 s | A sudden jump in users |
| `soak.properties` | 20 | 60 s | 4 h | 3–8 s | Leaks and slow degradation |

Don't run the full `load.properties` (300 users for an hour) casually against a laptop mock. Scale it down, for example `-Jusers=50 -Jduration=300`.

## Before a real load test

- **Listeners off.** In plan 10 they are disabled. Results go to the `.jtl` file.
- **Heap.** JMeter starts with a 1 GB heap. For big tests set the `HEAP` environment variable, for example `$env:HEAP="-Xms2g -Xmx4g"` (PowerShell) or `export HEAP="-Xms2g -Xmx4g"`.
- **Watch the load generator.** If its CPU is above about 80% or it runs out of memory, JMeter itself becomes the bottleneck and your response times are wrong. Use more machines (Tutorial 11).
- **Same environment, same data** for every run you compare.
- **Warm-up.** Exclude the ramp-up period when you judge steady-state numbers, or run a short warm-up first.
- **Tell people.** Agree the time window with the owners of the environment and its dependencies.

## The HTML dashboard

Open `results/smoke-report/index.html`. What to look at:

| Section | What it shows | What to look for |
|---|---|---|
| **Test and Report information** | Start and end time, file name | Is this the run you think it is? |
| **APDEX** | Satisfaction per label, with our thresholds (500 ms / 1500 ms) | Labels well below 1.0 |
| **Requests Summary** | Pass/fail pie | Any red at all |
| **Statistics** | Per label: samples, errors %, average, min, max, median, 90th, 95th, 99th pct, throughput, KB/s | The main table. Compare p95 to the SLO. |
| **Errors** / **Top 5 errors by sampler** | Error types and counts | Which errors, where, and how many |
| **Over Time → Response Times Over Time** | Each label's response time across the test | Climbing lines = degradation or queuing |
| **Over Time → Active Threads Over Time** | Users over time | Confirms your ramp-up and spike |
| **Throughput → Transactions Per Second** | TPS over time | Flat TPS while users rise = saturation |
| **Response Times → Response Time Percentiles** | The full percentile curve | A long tail at the right |
| **Response Times → Time Vs Threads** | Response time against active users | Where it starts to rise is your knee |

`report.properties` sets the Apdex thresholds, the report title, a 5-second graph granularity and which fields to save.

### Generate a report from an existing results file

```powershell
jmeter -g results/smoke.jtl -o results/smoke-report-again -q test-plans/report.properties
```

## The Aggregate Report and our summary script

The GUI's **Aggregate Report** listener (open a `.jtl` with *Browse…*) shows the same per-label numbers: samples, average, median, 90%, 95%, 99% lines, min, max, error %, throughput and KB/s.

`scripts/jtl_summary.py` prints the same table in the terminal (or as Markdown) and can **fail the build** on thresholds:

```powershell
python scripts/jtl_summary.py results/smoke.jtl --p95-max 3000 --error-max 1
python scripts/jtl_summary.py results/smoke.jtl --p95-max-label "TX03_Claims_Summary=3000"
```

It uses nearest-rank percentiles, so its numbers can differ from the HTML report by a few milliseconds.

## Check yourself

1. Why must the `-o` folder be empty?
2. Which command rebuilds the HTML report from yesterday's `.jtl` without re-running the test?
3. Your laptop's CPU was at 100% during a test. Can you trust the response times?

<details><summary>Answers</summary>

1. JMeter refuses to overwrite an existing report so you don't lose one by accident (use `-f` to delete it first).
2. `jmeter -g yesterday.jtl -o new-report-folder`
3. No. The load generator was saturated, so part of the measured time is JMeter waiting for CPU. Reduce the load per machine or add load generators.
</details>

**Next:** [11 · Distributed testing](11-distributed-testing.md)
