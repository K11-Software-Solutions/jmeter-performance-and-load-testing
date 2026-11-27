# 06 · Assertions

> **Goal:** make JMeter check that each response is *correct*, not just that it arrived, including negative tests that *expect* an error.
>
> **Script:** `test-plans/06_assertions.jmx` · **Data:** `test-plans/data/negative_cases.csv`

## Why assertions matter in performance tests

By default JMeter only fails a sample on a connection error or an HTTP 4xx/5xx code. A login page, an empty JSON body or `{"error":"..."}` with status 200 all count as **fast successes**, and they make results look *better* as the system breaks. Assertions stop that.

Keep them light during big load tests: every assertion costs CPU on the load generator. Check the status code plus one or two key facts per response.

## The assertions in plan 06

Thread group **Positive checks**:

| Assertion | Checks | Plan 06 example |
|---|---|---|
| **Response Assertion** | Response code, body text, headers or message: *equals*, *contains*, *matches* (regex), *substring*, optionally *not* | status `200`; body contains `"totalPaid"` |
| **JSON Assertion** | A JSON path exists, or equals an expected value | `$.user` equals `${username}` |
| **Duration Assertion** | The response took no longer than N ms | under 2000 ms |
| **Size Assertion** | The response size compared to N bytes | under 20 KB (catches unpaged results) |
| **JSR223 Assertion** | Any rule you can write in Groovy | `totalPaid` equals the sum of the monthly rows |

The JSR223 assertion is a **data accuracy** check, which matters for analytics products: under load a report must still be *right*, not just fast.

```groovy
import groovy.json.JsonSlurper
def json = new JsonSlurper().parseText(prev.getResponseDataAsString())
def sum = json.byMonth.collect { it.paid as BigDecimal }.sum().setScale(2, java.math.RoundingMode.HALF_UP)
def total = (json.totalPaid as BigDecimal).setScale(2, java.math.RoundingMode.HALF_UP)
if (sum != total) {
    AssertionResult.setFailure(true)
    AssertionResult.setFailureMessage("totalPaid " + total + " does not match sum of months " + sum)
}
```

`BigDecimal`, not `double`, because money needs exact decimals.

## Negative tests: expecting an error

Thread group **Negative checks** reads `negative_cases.csv`:

```
case,providerId,from,to,expectedStatus
unknown provider,P9999,2026-01-01,2026-01-31,404
missing provider,,2026-01-01,2026-01-31,400
bad date format,P1001,01/01/2026,2026-01-31,400
from after to,P1001,2026-02-01,2026-01-01,400
```

The trick is the Response Assertion's **Ignore Status** box (`Assertion.assume_success`). It tells JMeter "don't fail this sample just because it is a 4xx; let my assertion decide", and the assertion then checks the code equals `${expectedStatus}`.

Thread group **Security check** calls `/api/dashboard` with no token and expects **401**.

The CSV uses *Recycle on EOF = False* and *Stop thread on EOF = True*, so each case runs exactly once. The sampler name `GET claims-summary: ${case}` puts the case name in the results.

The plan sets **Run Thread Groups consecutively** on the Test Plan, so the three groups run one after another.

## Run it

```powershell
jmeter -n -t test-plans/06_assertions.jmx -l results/06.jtl
python scripts/jtl_summary.py results/06.jtl --fail-on-errors
```

To see an assertion fail, edit `negative_cases.csv` and change one `expectedStatus`, or run the mock with `LATENCY_FACTOR=20` so the Duration Assertion trips.

## Where to see failures

- View Results Tree → **Assertion result** tab
- The `.jtl` file's `failureMessage` column
- HTML report → **Errors** and **Top 5 errors by sampler** tables

## Check yourself

1. A load test shows 0% errors and 30 ms responses, but users say the report is broken. What might be missing?
2. How do you assert that an endpoint correctly returns 404?

<details><summary>Answers</summary>

1. Assertions on content. The server may be returning an error message or empty body with status 200.
2. A Response Assertion on the response code with *Ignore Status* ticked and the pattern `404`.
</details>

**Next:** [07 · Timers, think time and pacing](07-timers-think-time-and-pacing.md)
