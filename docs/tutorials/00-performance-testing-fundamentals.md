# 00 · Performance testing fundamentals

> **Goal:** understand *why* we run performance tests, the main test types, the numbers we measure, and how to turn business expectations into a workload model, before we open JMeter.

## Why performance testing matters

A feature can pass every functional test and still fail in production because it is too slow, falls over at peak, or slowly runs out of memory. Performance testing answers questions like these:

- Can the system handle the **expected peak** (for example 300 analysts opening reports at 9 a.m.) within the agreed response times?
- **Where does it break**, and how does it fail? Does it slow down gracefully or start returning errors?
- Does it **stay healthy over time**, or does memory, disk or connection usage creep up?
- Did the last release make it **slower** than the one before?

Performance is a quality attribute like correctness. In an analytics product a report that takes 30 seconds is a defect, even if the numbers are right.

## The main test types

| Type | Question it answers | Typical shape | What you watch |
|---|---|---|---|
| **Smoke (performance)** | Does the script work, and is the system basically healthy after a deploy? | A few users for 1–10 minutes | Errors, obvious slowness |
| **Load** | Do we meet our targets at the *expected* peak? | Ramp up to peak users, hold 30–60+ minutes | Percentiles against SLOs, error rate, throughput |
| **Stress** | Where is the breaking point, and how does the system fail and recover? | Increase load step by step beyond peak | The "knee" where throughput stops growing, error types, recovery |
| **Spike** | What happens when load jumps suddenly? | Steady load, then a burst of users in seconds | Errors and response time during and after the burst, auto-scaling |
| **Soak / endurance** | Does it stay stable over hours? | Normal load for 4–24 hours | Memory, connections, disk, slowly rising response times |
| **Scalability** | Does adding resources add capacity? | Repeat a step test with 1, 2, 4 instances | Throughput per instance, cost per request |

In this repo the same script (`test-plans/10_claims_summary_load.jmx`) runs as any of these, because every setting is a property. The profiles in `test-plans/profiles/` are the different shapes.

## Key metrics

**Response time (latency).** How long one request takes, from sending it to receiving the full response. JMeter calls this *elapsed time*. JMeter also records *latency* (time to first byte) and *connect time*.

**Percentiles (p90, p95, p99).** Sort all the response times. The 95th percentile (p95) is the value that 95% of requests were at or below. If p95 is 1.2 s, then 1 in 20 requests took longer than 1.2 s.

Why not the average? Averages hide slow users. Ten requests at 100 ms and one at 10 s average about 1 s, which describes nobody. Targets are normally set on p90 or p95, with p99 watched for the long tail.

**Throughput.** Work completed per unit of time, usually requests (or transactions) per second. Throughput is what the system *delivers*, not what you *send*.

**Error rate.** Failed samples ÷ all samples. In JMeter a sample fails if it gets a connection error, an HTTP error code (4xx/5xx), or fails an assertion. Always ask *which* errors: 401s from a broken script mean something very different from 503s under load.

**Concurrency (virtual users).** The number of users active at the same time. In JMeter, one thread = one virtual user.

**Apdex.** A 0–1 user-satisfaction score. You pick a threshold T (for example 500 ms):

- *Satisfied*: response time ≤ T
- *Tolerating*: between T and a second threshold (classically 4T; JMeter lets you set it, we use 1500 ms)
- *Frustrated*: above that, or an error

`Apdex = (satisfied + tolerating ÷ 2) ÷ total`. 1.0 is perfect; below about 0.7 users are unhappy. JMeter's HTML report shows Apdex per transaction.

**Server-side metrics.** JMeter tells you *that* something is slow. CPU, memory, garbage collection, database connection pool usage, slow-query logs, queue depths and cloud metrics (for example CloudWatch) tell you *why*. Always collect both. The mock API in this repo exposes `/metrics` so you can practise this.

## SLOs and targets

A **Service Level Objective (SLO)** is a measurable target that the team agrees on. A good performance SLO names the transaction, the percentile, the load and the error budget, for example:

> Claims Summary report: p95 under 3 s and error rate under 1% at 300 concurrent users.

That is the target we use in this repo's examples. "The page should be fast" is not a target.

Where targets come from: production analytics (APM, access logs), product owners, contracts, and the previous release as a baseline. If nobody has a number, propose one and get it agreed in writing before the test, not after.

## Workload modelling

The workload model describes *what real users do*, so the test reproduces it. Build it from data, not guesses:

1. **Who are the users and how many at peak?** Peak concurrent users, not total registered users.
2. **What do they do?** The main business transactions, for example Login, Open Dashboard, Run Claims Summary, Export Report.
3. **In what mix?** For example 50% dashboard, 35% claims summary, 15% export, from analytics or logs.
4. **How fast?** Think time between actions, session length, and the arrival rate at peak.
5. **With what data?** Different users, providers and date ranges, so caches don't make results look better than reality.

### Little's Law: the one formula worth remembering

For a system in a steady state:

```
Users (N) = Throughput (X) × (Response time (R) + Think time (Z))
```

Example: 300 concurrent users, about 0.5 s average response time and 5.5 s average think time (3–8 s random):

```
X = N ÷ (R + Z) = 300 ÷ (0.5 + 5.5) = 50 actions per second
```

So the test must deliver about 50 user actions per second at peak. If production logs show 80 per second at peak, either the user count or the think time in your model is wrong. Little's Law lets you sanity-check a model before you run it, and it explains why removing think time makes 300 threads generate far more load than 300 real people.

## Think time and pacing

- **Think time** is the pause between a user's actions (reading the screen, typing). Without it, each thread hammers the server as fast as it can, and 300 threads behave like thousands of real users.
- **Pacing** controls how often an *iteration* starts. For example, "each user starts a new session every 60 s, however long the session took". Pacing gives a steady arrival rate, which is useful when the business target is "N transactions per hour".

Tutorial 07 shows both in JMeter.

## Open and closed workload models

- **Closed model:** a fixed number of users who loop. A new request only starts when the previous one finishes, so when the server slows down, load drops. This is the default JMeter Thread Group.
- **Open model:** requests arrive at a set rate whatever the server does, like real internet traffic. When the server slows down, requests pile up. JMeter approximates this with throughput timers, or with the Open Model Thread Group added in JMeter 5.5.

Knowing which one you are running matters when you explain results: in a closed model, falling throughput under stress can simply mean your threads are stuck waiting.

## Where performance tests fit in CI/CD

| Stage | Performance check |
|---|---|
| Pull request | Optional: a 1-minute smoke against a local mock or ephemeral environment (this repo's GitHub Actions workflow) |
| Deploy to QA / staging | A 5–10 minute smoke or baseline with pass/fail thresholds |
| Nightly | A longer load test, with trends compared against the last good run |
| Release candidate | The full load, stress, spike and soak tests against a production-like environment |
| Production | Synthetic monitoring and alerts, not load tests (unless planned with operations) |

Rules that keep this healthy: run in non-GUI mode, keep thresholds in code, publish the HTML report as an artifact, and only compare runs made in the same environment with the same data.

## A safe test target

Only load-test systems you own or have written permission to test. Load testing someone else's site can look exactly like a denial-of-service attack. Everything in this repo runs against the **local mock API** in `mock-server/`, which uses synthetic data only.

## Check yourself

1. Why is p95 a better target than the average?
2. A stress test shows throughput flat at 160 req/s from 200 to 300 users while p95 triples. What does that suggest?
3. 200 users, 1 s response time, 9 s think time: roughly what throughput should you expect?
4. What is the difference between a load test and a soak test?

<details><summary>Answers</summary>

1. The average hides the slow tail; p95 tells you what the slowest 5% of users experience.
2. A bottleneck: requests are queuing for a limited resource (connections, threads, CPU, locks).
3. 200 ÷ (1 + 9) = 20 requests per second.
4. A load test checks targets at expected peak for a typical duration; a soak test runs normal load for many hours to find leaks and slow degradation.
</details>

**Next:** [01 · Install JMeter and run the mock API](01-install-jmeter-and-run-the-mock.md)
