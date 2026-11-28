# 15 · Cheat sheet and interview Q&A

> Quick reference for the night before an interview, and the questions a technical interviewer uses to check real JMeter experience.

## Command line

```powershell
# Run a test (non-GUI), write results and log
jmeter -n -t plan.jmx -l results.jtl -j jmeter.log

# ...and build the HTML dashboard at the end (folder must be new or empty; -f clears old output)
jmeter -n -t plan.jmx -l results.jtl -e -o report -f

# Override properties read with ${__P(name,default)}
jmeter -n -t plan.jmx -Jusers=200 -Jrampup=300 -Jduration=1800 -l results.jtl

# Load a property file (profiles, report settings); several -q are allowed
jmeter -n -t plan.jmx -q profiles/load.properties -q report.properties -l results.jtl

# Build the HTML report later from an existing results file
jmeter -g results.jtl -o report

# Distributed: run on remote load generators, send a property to all of them, stop them at the end
jmeter -n -t plan.jmx -R 10.0.0.11,10.0.0.12 -Gusers=100 -l results.jtl -X

# More memory for JMeter (PowerShell / bash)
$env:HEAP="-Xms2g -Xmx4g"
export HEAP="-Xms2g -Xmx4g"
```

## This repo's helpers

```powershell
node mock-server/server.js                                  # start the target
python scripts/run_tutorials.py                              # run plans 01-10, fail on any error
python scripts/jtl_summary.py results.jtl --p95-max 3000 --error-max 1
python scripts/step_load.py --users 10 20 40 80 160          # stress test, one table
```

## Elements in one line each

| Element | One line |
|---|---|
| Thread Group | Virtual users, ramp-up, loops or duration |
| setUp / tearDown Thread Group | Runs before / after the normal groups (seed data, shared token, clean up) |
| HTTP Request Defaults | Host, port, protocol and timeouts for every HTTP sampler in scope |
| HTTP Header Manager | Headers such as `Content-Type` and `Authorization: Bearer ${token}` |
| HTTP Cookie Manager | Stores cookies per thread, like a browser |
| CSV Data Set Config | One row per thread per iteration, from a file |
| JSON / Regex / Boundary Extractor | Correlation: capture a value into a variable |
| Response / JSON / Duration / Size Assertion | Fail the sample when the response is wrong, slow or too big |
| Uniform / Gaussian Random Timer | Random think time |
| Constant Throughput / Precise Throughput Timer | Hold a target rate (they can only slow threads down) |
| Flow Control Action | A "do nothing" sampler to hang timers on, or to pause/stop threads |
| Transaction Controller | Time a group of requests as one business transaction |
| Once Only / Loop / While / ForEach / If / Switch | Flow control |
| JSR223 (Groovy) elements | Custom logic: `vars`, `props`, `prev`, `log` |
| View Results Tree / Summary / Aggregate Report | Debugging in the GUI only |
| Backend Listener | Stream live metrics to InfluxDB/Graphite |

## Functions

| Function | Example |
|---|---|
| Property with default | `${__P(users,10)}` |
| Random number | `${__Random(1,100)}` |
| UUID | `${__UUID()}` |
| Date/time | `${__time(yyyy-MM-dd)}`, `${__timeShift(yyyy-MM-dd,,P-1D,,)}` |
| Thread number | `${__threadNum}` |
| Expression | `${__jexl3(${count} > 5)}`, `${__groovy(vars.get('a').toUpperCase())}` |
| Counter | `${__counter(FALSE,)}` (shared) / `${__counter(TRUE,)}` (per thread) |

## Numbers to read in a report

| Metric | Healthy pattern | Warning sign |
|---|---|---|
| p90 / p95 / p99 | Flat as load grows, under the SLO | Rising steeply with users |
| Throughput | Grows in step with users | Flattens or drops while users keep rising |
| Error % | 0, or explained (expected 4xx in negative tests) | Grows with load; 5xx, timeouts, connection resets |
| Active threads | Matches the plan | Fewer than planned (threads died, generator overloaded) |
| Response time vs threads | Flat, then a gentle rise | A sharp "knee" |
| Load generator CPU | Below about 80% | Near 100%: results are not trustworthy |

## Little's Law

```
Users = Throughput × (Response time + Think time)
```

300 users, 0.5 s response, 5.5 s think → 300 ÷ 6 = **50 requests per second**.

---

## Interview Q&A

Short, honest answers you can say in your own words. Links point to the tutorial with more detail.

### Fundamentals

**1. What is the difference between load, stress, spike, soak and scalability testing?**
Load: expected peak, to confirm targets. Stress: beyond peak, to find the breaking point and how it fails and recovers. Spike: a sudden jump in users. Soak: normal load for hours, to find leaks. Scalability: does adding resources add capacity? ([00](00-performance-testing-fundamentals.md))

**2. Why are p90/p95 more useful than the average?**
The average hides the slow tail. p95 tells you what the slowest 1 in 20 requests experienced, which is what users complain about.

**3. What is throughput, and how is it different from the number of users?**
Throughput is completed requests per second, what the system delivers. Users are concurrent sessions. With think time, 300 users might generate only 50 requests per second (Little's Law).

**4. How do you build a workload model?**
From production data or the product team: peak concurrent users, the main transactions, their mix, think time, session length and test data. Then sanity-check it with Little's Law against the expected throughput.

**5. What is Apdex?**
A 0–1 satisfaction score: (satisfied + tolerating ÷ 2) ÷ total, using a response-time threshold T. JMeter's HTML report shows it per transaction.

**6. What is an SLO? Give an example.**
A measurable target: "Claims Summary p95 under 3 s and errors under 1% at 300 concurrent users."

**7. Open versus closed workload model?**
Closed: a fixed number of users who wait for each response, so load drops when the server slows. Open: requests arrive at a set rate regardless, so queues build. The default Thread Group is closed; throughput timers or the Open Model Thread Group approximate open.

### JMeter mechanics

**8. Walk me through how you build a JMeter test.**
Workload model first. Then a Thread Group sized to the model; HTTP Request Defaults, Header and Cookie Managers; samplers grouped into Transaction Controllers; CSV data; correlation with extractors; assertions on status and key content; random think time. Debug with a few users and View Results Tree, then disable listeners and run in non-GUI mode with the HTML report. ([10](10-non-gui-runs-and-html-dashboard.md))

**9. What is the difference between ramp-up and duration?**
Ramp-up is how long it takes to *start* all the threads. Duration is how long the thread group runs in total.

**10. Why not run load tests in GUI mode?**
The GUI and listeners use CPU and memory on the load generator, which slows JMeter itself and distorts results.

**11. What is a `.jtl` file?**
JMeter's results file: one row per sample with timestamp, elapsed, label, response code, success, bytes, latency, connect time and thread counts. You can build the HTML report from it with `-g`.

**12. Parameterisation versus correlation?**
Parameterisation feeds input data you control (CSV). Correlation captures dynamic values from responses (tokens, IDs) and passes them on. ([04](04-parameterisation-with-csv.md), [05](05-correlation.md))

**13. How do you find what needs correlating?**
Record or run the flow twice and compare; look for values in requests that first appeared in an earlier response. Extract with a JSON or regex extractor with a clear default, and assert on the next request.

**14. JSON Extractor match number 0, 1 and -1?**
0 = a random match, 1 = the first, -1 = all matches as `name_1…name_N` plus `name_matchNr` (for a ForEach Controller).

**15. How do you share a token across all threads?**
Log in once in a setUp Thread Group and store it with `props.put()`, then use `${__P(sharedToken)}`. Or let each thread log in and extract its own token, which is more realistic when login is part of the load. ([09](09-jsr223-and-groovy.md))

**16. What does the Constant Throughput Timer do?**
It pauses threads so the group sends about N samples per minute. It can only slow threads down, so you need enough threads to reach the target. ([07](07-timers-think-time-and-pacing.md))

**17. Think time versus pacing?**
Think time is the pause between actions. Pacing fixes how often an iteration starts, keeping the arrival rate steady even when response times change.

**18. How do you implement a 50/35/15 transaction mix?**
A Switch Controller with a weighted random value picks exactly one action per loop (plan 10). Throughput Controllers in percent mode also work, but each decides independently. ([08](08-logic-controllers.md))

**19. How do you test that an endpoint correctly returns an error?**
A Response Assertion on the response code with *Ignore Status* ticked, expecting e.g. 404. ([06](06-assertions.md))

**20. Why use Groovy rather than BeanShell, and what is the main JSR223 mistake?**
Groovy is compiled and cached, so it is much faster. The mistake is putting `${var}` inside the script; use `vars.get('var')` instead.

**21. What are JMeter's limits, and how do you generate a large load?**
One machine runs out of CPU, memory or network at high thread counts. Use non-GUI mode, no listeners, a bigger heap, and distributed testing with several load generators, while watching their CPU. ([11](11-distributed-testing.md))

**22. How does distributed testing work?**
A controller sends the plan to load generators running `jmeter-server`. Each generator runs the full thread count, so 3 generators × 100 users = 300 users. Results stream back to the controller. CSV files must exist on every generator, and versions must match.

### Results and bottlenecks

**23. How do you analyse JMeter results?**
Percentiles against the SLO, throughput against the target, error rate and error types, and how response time and throughput change as load increases. Then correlate with server metrics: CPU, memory, GC, connection pools, database and cloud metrics. ([14](14-reading-results-and-finding-bottlenecks.md))

**24. What does it mean when throughput flattens while response time climbs?**
Saturation. Requests are queuing for a limited resource such as a connection pool, thread pool, CPU or lock. Adding users only adds waiting time.

**25. What are common causes of bottlenecks?**
Small connection or thread pools, missing indexes, N+1 queries, slow downstream calls made synchronously, no caching, large unpaged results, lock contention, memory leaks and GC pauses (often visible only in soak tests).

**26. Tell me about a bottleneck you found.** *(fill in with your own real example)*
"On [service], at around [N users], [transaction] p95 went from [X] to [Y] while throughput flattened at [Z] per second. Server metrics showed [cause]. After [fix], the same test gave p95 [W] at [load]."
If your strongest real story is older, practise with the step test in this repo, and say honestly that it is a lab exercise: "In my lab against a mock with a 4-connection pool, throughput flattened at about 45 req/s and the server queue grew to 62…"

**27. The test fails the target. What do you report?**
The facts with graphs: at which load the SLO breaks, which transaction, the error types, the evidence of the cause, and a clear statement such as "the system currently supports about 200 users within target, not 300", plus the next step.

**28. How do you know the load generator was not the bottleneck?**
Monitor its CPU, memory and network during the run; check active threads matched the plan; compare with a run from a second generator.

**29. What would you check in a soak test?**
Memory and heap after GC, connection counts, thread counts, disk and log growth, and whether response times creep up over hours.

**30. Response time is fine but errors are 3%. What next?**
Look at which errors (status codes, messages, which transactions, when they started). 5xx under load points to the server; 401/403 to correlation or session problems; connection resets or timeouts to network, pools or the generator.

### CI/CD and process

**31. How do you run JMeter in CI/CD?**
Non-GUI from the pipeline: a short smoke on every deployment to QA, the full load before release. Thresholds (p95, error rate) fail the stage, and the HTML report is published as an artifact. ([12](12-ci-with-github-actions.md))

**32. Why doesn't a CI job fail on its own when samples fail?**
JMeter exits with 0 even if samples fail. You need an explicit gate, such as a results check script or plugin.

**33. How do you make results comparable between runs?**
Same environment, data volume, script version, load profile and duration; a warm-up; exclude ramp-up from steady-state numbers; keep baselines and compare against them.

**34. How do you handle PHI or PII in performance tests?**
Use synthetic or approved masked data, never real PHI in CSV files, logs, reports or screenshots, and keep results with sensitive URLs out of public artifacts.

**35. How would you load-test an AI feature (for example a Bedrock summary)?**
The same principles, plus: much longer and more variable response times, streaming responses, rate limits and throttling, and cost per request. Assert on response structure, measure time to first token if it streams, and agree a budget for the test because each call costs money.

## Next: the same scenario in k6

Want to compare tools? The companion repo [k6-performance-and-load-testing](https://github.com/K11-Software-Solutions/k6-performance-and-load-testing) rebuilds this workload in Grafana k6. Its Tutorial 15 maps every JMeter element on this page to its k6 equivalent.

**Previous:** [14 · Reading results and finding bottlenecks](14-reading-results-and-finding-bottlenecks.md) · **Back to the [learning path](../../README.md#learning-path)**
