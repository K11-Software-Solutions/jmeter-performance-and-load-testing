# 12 · CI integration with GitHub Actions

> **Goal:** run a JMeter smoke test automatically on every push and pull request, fail the build when thresholds are breached, and publish the HTML report.
>
> **Workflow:** `.github/workflows/jmeter-smoke.yml`

## What the workflow does

| Step | What happens |
|---|---|
| Check out, set up Java 17 and Node 20 | Tools for JMeter and the mock |
| Cache JMeter | The JMeter download is cached between runs |
| Download and verify JMeter | From `archive.apache.org`, with a SHA-512 check |
| Start the mock API | `node mock-server/server.js` in the background, then waits for `/health` |
| Run the smoke test | Plan 10 with `profiles/smoke.properties`, non-GUI, with `-e -o` for the HTML report |
| Check thresholds | `scripts/jtl_summary.py --p95-max 1500 --error-max 1`; a breach fails the job |
| Job summary | The results table is added to the run's summary page |
| Upload artifact | `jmeter-html-report`: the HTML dashboard, `.jtl`, logs (kept 14 days) |

It runs on push to `main`, on every pull request, and on demand. **Run workflow** lets you change users, duration and thresholds, and tick *run_tutorials* to also run plans 01–10.

## Reading the result

1. Open the **Actions** tab → *JMeter performance smoke test* → a run.
2. The summary page shows the results table.
3. Download **jmeter-html-report**, unzip it, and open `html-report/index.html`.

## Why thresholds live in the pipeline

JMeter's exit code is 0 even when samples fail, so a pipeline that only runs JMeter will always be "green". You need an explicit gate. Choices:

- **A results check after the run** (this repo): parse the `.jtl` and fail on p95 or error rate.
- **Assertions in the plan**, for example a Duration Assertion, plus failing the job when errors exist.
- **Plugins or tools** such as Taurus, or the `jmeter-maven-plugin` (an example is in `jmeter-mvn-example-master/`), which can fail a Maven build.

Good thresholds are tied to the SLO, are a little looser for smoke tests in shared CI runners (they are noisy), and are reviewed when the system changes.

## Smoke in CI, load somewhere else

A GitHub-hosted runner is a small shared VM. It is fine for a **smoke** test that proves the script and catches big regressions. It is not a place for a real load test:

- results vary with the runner's neighbours,
- network latency to your environment is unknown,
- you can't generate serious load from one small VM.

Run real load tests from dedicated load generators close to a production-like environment, triggered by the pipeline before a release.

## Same idea in other CI tools

Jenkins, Azure Pipelines and GitLab use the same three commands: start the target (or point at the environment), run `jmeter -n … -e -o report`, then check thresholds and publish the report. The prep guide's Azure Pipelines example:

```yaml
- job: Performance
  steps:
  - script: |
      jmeter -n -t perf/claims_summary.jmx -l results.jtl -e -o perf-report -Jusers=50 -Jduration=600
    displayName: 'JMeter performance check'
  - publish: perf-report
    artifact: jmeter-report
```

## Exercise

1. Open a pull request with a small change and watch the workflow run.
2. Use *Run workflow* with `p95_max_ms = 50`. The job should fail on thresholds. Read the message.
3. Start the mock with `LATENCY_FACTOR=10` in the workflow file (on a branch) and see the report change.

**Next:** [13 · Backend Listener, InfluxDB and Grafana (optional)](13-backend-listener-influxdb-grafana.md)
