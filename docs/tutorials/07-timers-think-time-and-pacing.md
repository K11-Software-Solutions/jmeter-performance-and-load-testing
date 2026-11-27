# 07 · Timers, think time and pacing

> **Goal:** control *how fast* virtual users send requests: random think time, a target throughput, and pacing per iteration.
>
> **Script:** `test-plans/07_timers.jmx` (four short thread groups that run one after another, about 1 minute in total)

## Why timers matter

Without timers, each thread sends its next request the moment the last one finishes. Ten threads with no think time can send as much traffic as hundreds of real users (see Little's Law in Tutorial 00). Your model then has nothing to do with reality.

## How timers work in JMeter

- A timer **delays the sampler it is attached to** (it runs before the sampler).
- If a timer is at Thread Group level, it applies before **every** sampler in its scope.
- Several timers in scope **add up**.
- Timer time is **not** included in the sample's response time. Transaction Controllers leave it out too, unless you tick *Include duration of timer and pre-post processors*.

To pause *between* steps without tying the delay to a particular request, put the timer under a **Flow Control Action** sampler (pause 0 ms). Plans 02, 03 and 10 do this. A Flow Control Action does not appear in the results.

## The four thread groups

### A · Precise Throughput Timer: a target rate (120 per minute)

The **Precise Throughput Timer** schedules requests to hit a target rate (here 120 per 60 s = 2 per second) with random, Poisson-style arrivals. It gives a more realistic arrival pattern than the Constant Throughput Timer and is the usual choice for an "open" workload model.

> **Gotcha we found while building this repo:** the Precise Throughput Timer's schedule starts when the **test** starts, not when its own thread group starts. When this group ran third, it fired all the requests it had "missed" in one burst to catch up (about 6 per second instead of 2). That's why it now runs first. In your own plans, give it its own thread group that starts with the test.

### B · Constant Throughput Timer: a target rate (60 per minute)

The **Constant Throughput Timer** pauses threads so the group sends about **N samples per minute** in total. Here: 60 per minute shared by all active threads in the group, so about 1 per second.

Important: a throughput timer can only **slow threads down**. If 5 threads can't reach the target because the server is slow, add threads. A common sizing rule is threads ≈ target per second × (response time + think time) in seconds, plus some spare.

### C · Think time: Uniform and Gaussian random timers

| Timer | Delay | Plan 07 |
|---|---|---|
| **Constant Timer** | Always N ms | 500 ms between export polls (plans 08, 10) |
| **Uniform Random Timer** | Constant offset + random 0…range ms | 1000 ms + up to 2000 ms (1–3 s) |
| **Gaussian Random Timer** | Constant offset ± normal distribution with the given deviation | 1500 ms ± 300 ms |

Random think time stops all users acting in lock-step, which would create artificial waves of load.

The main load test (plan 10) uses a Uniform Random Timer of `THINK_MIN_MS + up to THINK_RANGE_MS` = 3000 + 0–5000 ms, which is the **3–8 s think time** from the workload model.

### D · Pacing with a JSR223 Timer

Pacing fixes how often an **iteration** starts. Here each user starts a new iteration every 2 s, however long its requests took:

```groovy
// JSR223 Timer: return the delay in milliseconds
long pacing = 2000L
long elapsed = System.currentTimeMillis() - (vars.get('iterStart') as long)
vars.put('newIteration', 'true')
return Math.max(0L, pacing - elapsed)
```

A JSR223 PreProcessor records `iterStart` at the first request of each iteration. Use pacing when the business target is "N sessions per hour" and you want that rate to stay steady even when response times change.

## Run it and compare

```powershell
jmeter -n -t test-plans/07_timers.jmx -Jtg_duration=20 -l results/07.jtl
python scripts/jtl_summary.py results/07.jtl
```

Look at the **Throughput/s** column. In our run (15 s per group) we saw about 2.5/s for A (the target is 2/s; the first second or two of start-up adds a little), about 1.1/s for B, about 1/s per label for C, and about 1.2/s per label for D (2 users, one iteration every 2 s each).

## Check yourself

1. You set a Constant Throughput Timer to 6000 per minute with 10 threads, and reach only 900 per minute. Why?
2. Does a timer's delay count in the sample's response time?

<details><summary>Answers</summary>

1. Throughput timers only slow threads down. 10 threads can't send 100 requests per second if each request plus think time takes over 100 ms; add threads.
2. No. It is added before the sampler and is not part of the sample's elapsed time.
</details>

**Next:** [08 · Logic controllers](08-logic-controllers.md)
