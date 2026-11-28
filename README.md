<p align="center">
  <img src="docs/images/k11_logo.png" alt="K11 Software Solutions" width="120">
</p>

<h1 align="center">JMeter Performance and Load Testing: Beginner to Advanced</h1>

<p align="center">
  A hands-on learning path from K11 Tech Lab: performance-testing fundamentals, 13 numbered JMeter tutorials with runnable scripts, a safe local mock API, CI with GitHub Actions, and a worked example of reading results and finding a bottleneck.
  <br>Companion: <a href="https://github.com/K11-Software-Solutions/k6-performance-and-load-testing">k6-performance-and-load-testing</a>, the same mock API and scenario in Grafana k6, so you can compare the two tools on the same system.
</p>

<p align="center">
  <a href="docs/JMeter_Performance_Testing_Guide.pdf"><b>📘 Download the PDF guide</b></a> ·
  <a href="#learning-path">Learning path</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="docs/tutorials/15-cheat-sheet-and-interview-qa.md">Cheat sheet and interview Q&amp;A</a>
</p>

---

## What's inside

| Folder | Contents |
|---|---|
| [`docs/tutorials/`](docs/tutorials/) | 16 Markdown tutorials (00–15), each with a goal, hands-on steps, exercises and self-check questions |
| [`test-plans/`](test-plans/) | Runnable JMeter 5.6.3 `.jmx` scripts, one or more per tutorial |
| [`test-plans/data/`](test-plans/data/) | Synthetic CSV test data (users, date ranges, negative cases) |
| [`test-plans/profiles/`](test-plans/profiles/) | Smoke, load, stress, spike and soak settings for the same script |
| [`mock-server/`](mock-server/) | A local, dependency-free Node.js API to test against, with a built-in connection-pool bottleneck |
| [`scripts/`](scripts/) | Python helpers: run all tutorials, summarise results with percentiles and thresholds, run a step (stress) test |
| [`results/sample/`](results/sample/) | A real step-test result set from the mock, used in the worked example |
| [`observability/`](observability/) | Optional InfluxDB + Grafana stack for live results |
| [`.github/workflows/`](.github/workflows/) | Non-GUI smoke test on every push and PR, with thresholds and the HTML report as an artifact |
| [`docs/JMeter_Performance_Testing_Guide.pdf`](docs/JMeter_Performance_Testing_Guide.pdf) | The whole path as a designed PDF guide |

> **Safe by design.** Every script targets the local mock API in `mock-server/`, never a real website. Only load-test systems you own or have written permission to test.

## Quick start

You need **Java 17+**, **Apache JMeter 5.6.3**, **Node.js 18+** and **Python 3.8+**. See [Tutorial 01](docs/tutorials/01-install-jmeter-and-run-the-mock.md) for installation.

```powershell
# 1. Start the mock API (leave it running)
node mock-server/server.js

# 2. In a second terminal: run the smoke test and build the HTML report
jmeter -n -t test-plans/10_claims_summary_load.jmx -q test-plans/profiles/smoke.properties -q test-plans/report.properties -l results/smoke.jtl -e -o results/smoke-report

# 3. Summarise it, with pass/fail thresholds
python scripts/jtl_summary.py results/smoke.jtl --p95-max 3000 --error-max 1

# 4. Or run every tutorial plan and check none of them fail
python scripts/run_tutorials.py
```

Open `results/smoke-report/index.html` to see JMeter's dashboard.

## Learning path

| # | Tutorial | Script(s) | You will learn |
|---|---|---|---|
| **Part 1 · Fundamentals** ||||
| 00 | [Performance testing fundamentals](docs/tutorials/00-performance-testing-fundamentals.md) | – | Test types, percentiles, throughput, Apdex, SLOs, workload modelling, Little's Law, think time, CI/CD |
| **Part 2 · JMeter basics** ||||
| 01 | [Install JMeter and run the mock API](docs/tutorials/01-install-jmeter-and-run-the-mock.md) | `01_hello_jmeter.jmx` | Install, GUI vs non-GUI, your first run |
| 02 | [Test plan anatomy](docs/tutorials/02-test-plan-anatomy.md) | `02_test_plan_anatomy.jmx` | Thread groups, samplers, config elements, listeners, scope, execution order |
| 03 | [Recording vs scripting](docs/tutorials/03-recording-vs-scripting.md) | `03_recorded_portal_flow.jmx` | The HTTP(S) Test Script Recorder and cleaning up a recording |
| 04 | [Parameterisation with CSV](docs/tutorials/04-parameterisation-with-csv.md) | `04_csv_parameterisation.jmx` | CSV Data Set Config, sharing modes, built-in functions |
| 05 | [Correlation](docs/tutorials/05-correlation.md) | `05_correlation.jmx` | JSON, Regular Expression and Boundary extractors |
| 06 | [Assertions](docs/tutorials/06-assertions.md) | `06_assertions.jmx` | Response, JSON, Duration, Size and JSR223 assertions; negative tests |
| **Part 3 · Building realistic tests** ||||
| 07 | [Timers, think time and pacing](docs/tutorials/07-timers-think-time-and-pacing.md) | `07_timers.jmx` | Random think time, throughput timers, pacing |
| 08 | [Logic controllers](docs/tutorials/08-logic-controllers.md) | `08_logic_controllers.jmx` | Transaction, Once Only, Loop, ForEach, If, While, Switch, Random, Throughput |
| 09 | [JSR223 and Groovy](docs/tutorials/09-jsr223-and-groovy.md) | `09_jsr223_groovy.jmx` | `vars`, `props`, `prev`; sharing a token across threads; business-rule checks |
| **Part 4 · Running at scale** ||||
| 10 | [Non-GUI runs and the HTML dashboard](docs/tutorials/10-non-gui-runs-and-html-dashboard.md) | `10_claims_summary_load.jmx` | The full workload model, profiles, CLI options, the HTML report |
| 11 | [Distributed testing](docs/tutorials/11-distributed-testing.md) | `10_claims_summary_load.jmx` | Controller and load generators, RMI, `-R` / `-G` |
| 12 | [CI with GitHub Actions](docs/tutorials/12-ci-with-github-actions.md) | `.github/workflows/jmeter-smoke.yml` | Smoke test in CI, thresholds, report artifact |
| 13 | [Backend Listener, InfluxDB and Grafana](docs/tutorials/13-backend-listener-influxdb-grafana.md) *(optional)* | `13_backend_listener_influxdb.jmx` | Live dashboards during long tests |
| **Part 5 · Results** ||||
| 14 | [Reading results and finding bottlenecks](docs/tutorials/14-reading-results-and-finding-bottlenecks.md) | `scripts/step_load.py` | Reading the dashboard, percentiles, the knee, a worked example with real data |
| 15 | [Cheat sheet and interview Q&A](docs/tutorials/15-cheat-sheet-and-interview-qa.md) | – | Commands, elements, functions and 30+ interview questions |

**Suggested pace:** Part 1 and tutorials 01–06 in week 1; 07–10 in week 2; 11–15 plus your own step test in week 3.

## The scenario

All examples follow one realistic scenario: a **healthcare claims analytics** web application. Analysts log in, open a dashboard, run the **Claims Summary** report for a provider and date range, and export it. The target is a typical one for this kind of report:

> **300 concurrent users at peak; Claims Summary p95 under 3 s; error rate under 1%.**
> Workload mix: Dashboard 50%, Claims Summary 35%, Export 15%; think time 3–8 s.

## How the scripts were checked

Every plan from 01 to 10 was run in non-GUI mode with **Apache JMeter 5.6.3** on Java 21 against the mock API, and finished with **0 failed samples** (`python scripts/run_tutorials.py`). Plan 13 (Backend Listener) was run without InfluxDB. The Docker-based InfluxDB/Grafana stack was not run during the build; see the note in Tutorial 13.

## Earlier course material in this repo

These folders were here before the learning path was added and are kept unchanged for reference:

- `Ex_Files_JMeter_Load_Testing/` and `Ex_Files_Adv_JMeter/`: exercise files from the online courses *JMeter: Performance and Load Testing* and *Advanced JMeter*, completed in May 2024 (they target the courses' own demo sites)
- `CertificateOfCompletion_*.pdf`: course completion certificates
- `jmeter-mvn-example-master/`: an example of running JMeter through the `jmeter-maven-plugin`

## Companion repo: k6

[**k6-performance-and-load-testing**](https://github.com/K11-Software-Solutions/k6-performance-and-load-testing) teaches the same material with Grafana k6: the same mock API, data and Claims Summary workload, rebuilt as k6 JavaScript, with thresholds as the CI gate and an **open-model** stress test. Its Tutorial 14 compares that run with this repo's closed-model step test, and its Tutorial 15 maps every JMeter concept to its k6 equivalent.

## About

Created by **Kavita Jadhav**, Founder & CEO of [K11 Software Solutions](https://github.com/K11-Software-Solutions) (K11 Tech Lab).

