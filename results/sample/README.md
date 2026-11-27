# Sample results

Real results from runs against the **local mock API on one laptop** (JMeter 5.6.3, Java 21, Windows 11), used in [Tutorial 14](../../docs/tutorials/14-reading-results-and-finding-bottlenecks.md). They are for learning to read results, **not benchmarks** of any real system.

All runs used `scripts/step_load.py` with `test-plans/10_claims_summary_load.jmx`, the stress profile (0.5–1.5 s think time) and 90 s per step.

| Folder | Mock settings | What it shows |
|---|---|---|
| `step-test/` | `POOL_SIZE=4 QUEUE_TIMEOUT_MS=2000` | **The main worked example.** 10 → 160 users: linear scaling, the knee at about 40 users, saturation at 80, 25% errors (503) at 160 |
| `after-fix-pool-8/` | `POOL_SIZE=8 QUEUE_TIMEOUT_MS=2000` | The re-test after "fixing" the bottleneck: capacity roughly doubles, no errors at 160 users |
| `unguarded-cascade/` | `POOL_SIZE=4 QUEUE_TIMEOUT_MS=2000` | An earlier version of plan 10 **without** If Controller guards: 727 real 503s became 3,210 failed samples through cascade 401/404 errors |
| `closed-model-5s-timeout/` | `POOL_SIZE=4 QUEUE_TIMEOUT_MS=5000` | The same steps with a longer timeout: the same bottleneck but **no** errors, because a closed workload model limits the queue |

Each folder has `step-summary.md` (all requests per step). `step-test/` and `after-fix-pool-8/` also have per-label tables (`users-N-by-label.md`), including the `TX` transactions.

Columns: *Server max queue* is the longest connection queue the mock has seen since it started (from `/metrics`); *Server 503s* is the number of 503 responses the mock sent during that step; *Successful (req/s)* excludes failed samples.

Your own numbers will differ a little; the shape of the curves should not.
