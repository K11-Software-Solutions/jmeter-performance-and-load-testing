# 08 · Logic controllers

> **Goal:** control *which* requests run, *how often* and *in what order*, so the script follows a realistic user journey.
>
> **Scripts:** `test-plans/08_logic_controllers.jmx` (one of each), `test-plans/10_claims_summary_load.jmx` (Switch Controller for the workload mix)

## The journey in plan 08

```
Thread Group: Analysts (3 users x 3 loops)
├── Once Only Controller: log in once per user
│   └── TX01_Login → POST /api/auth/login (JSON Extractor: token)
├── Loop Controller: refresh the dashboard twice
│   └── GET /api/dashboard
├── GET /api/providers (JSON Extractor, match no. -1 → providerIds_1 … providerIds_20)
├── ForEach Controller: first 3 providers (providerIds → currentProvider)
│   └── GET claims-summary for ${currentProvider} (JSON Extractor: reportId)
├── Random Controller: pick one action
│   ├── Random: GET /api/dashboard
│   └── Random: GET /api/providers
└── Throughput Controller: about 50% of iterations
    └── If Controller: only when we have a reportId
        └── TX02_Export_Report
            ├── POST .../export (exportId, exportStatus; pollCount = 0)
            ├── While Controller: poll until READY (max 10)
            │   └── GET /api/reports/exports/${exportId} (+ 500 ms timer, pollCount + 1)
            └── GET .../download (assert the CSV header)
```

## Controller reference

| Controller | Use it for | Plan 08 example |
|---|---|---|
| **Transaction Controller** | Group requests into one business transaction with its own timing | `TX01_Login`, `TX02_Export_Report` |
| **Once Only Controller** | Run something once per thread (on the first iteration) | Log in once |
| **Loop Controller** | Repeat children N times | Refresh the dashboard twice |
| **ForEach Controller** | Loop over variables `name_1`, `name_2`, … from an extractor with match no. -1 | Run the report for 3 providers |
| **Random Controller** | Run **one** child chosen at random each time | Dashboard or providers |
| **Throughput Controller** | Run children in a percentage of iterations, or a fixed number of times | Export in about 50% of iterations |
| **If Controller** | Run children only when a condition is true | Only export when a reportId exists |
| **While Controller** | Repeat until a condition becomes false | Poll the export status |
| **Switch Controller** | Run exactly one child, chosen by number or name | The weighted workload mix in plan 10 |
| **Interleave Controller** | Run a different child on each iteration, in turn | Not used here |
| **Runtime Controller** | Run children for N seconds | Not used here |
| **Simple Controller** | Just groups elements (no logic) | Not used here |

### Transaction Controller notes

- It reports the total time of its children as one sample. The HTML report shows transactions and individual requests side by side.
- Leave *Generate parent sample* unticked (as here) to keep both the transaction and its requests in the results. Tick it to see only the transaction, with the requests as sub-results.
- Timer time is excluded unless you tick *Include duration of timer…*.
- Use a naming convention, for example `TX01_Login`. The helper `scripts/jtl_summary.py` treats labels starting with `TX` as transactions and leaves them out of the "ALL REQUESTS" total, so requests are not counted twice.

### Writing conditions

Use `__jexl3` (or `__groovy`) and tick *Interpret condition as variable expression*:

```
${__jexl3("${reportId}" != "NOT_FOUND")}
${__jexl3("${exportStatus}" != "READY" && ${pollCount} < 10)}
```

Always add a **maximum** to While loops so a stuck export can't trap a thread forever.

## The workload mix (plan 10)

The workload model says 50% dashboard, 35% claims summary and 15% export. Plan 10 uses a **Switch Controller** whose value is a weighted random choice:

```
${__groovy(def r = java.util.concurrent.ThreadLocalRandom.current().nextInt(100);
  r < ${MIX_DASHBOARD} ? 'TX02_Dashboard' : (r < ${MIX_DASHBOARD} + ${MIX_CLAIMS} ? 'TX03_Claims_Summary' : 'TX04_Export_Report'))}
```

The Switch Controller runs the child whose **name** matches. Unlike three separate Throughput Controllers (which decide independently, so one iteration might run two actions or none), this picks exactly one action per loop and keeps the mix accurate. Change the mix with `-Jmix_dashboard=60 -Jmix_claims=30`.

## Run it

```powershell
jmeter -n -t test-plans/08_logic_controllers.jmx -l results/08.jtl
python scripts/jtl_summary.py results/08.jtl
```

Count the samples per label and match them to the controllers: 3 logins (Once Only), 18 dashboards (3 users × 3 loops × 2), 9 per provider (ForEach), and roughly half the iterations with an export.

**Next:** [09 · JSR223 and Groovy](09-jsr223-and-groovy.md)
