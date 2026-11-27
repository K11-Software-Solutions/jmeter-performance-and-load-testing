# 09 · JSR223 and Groovy

> **Goal:** use Groovy scripts for logic the standard elements can't do: dynamic data, parsing responses, business-rule checks and sharing data between threads.
>
> **Script:** `test-plans/09_jsr223_groovy.jmx`

## JSR223 elements

There is a JSR223 version of most element types: **Sampler, PreProcessor, PostProcessor, Assertion, Timer, Listener**. Always choose **Groovy** as the language. It is compiled and cached, so it is fast. BeanShell and JavaScript are much slower, and BeanShell is no longer recommended.

## Objects available in scripts

| Object | What it is | Example |
|---|---|---|
| `vars` | This thread's variables | `vars.get('token')`, `vars.put('x', '1')` |
| `props` | JMeter properties, shared by **all** threads | `props.put('sharedToken', t)` |
| `prev` | The previous sample result (post-processors, assertions) | `prev.getResponseDataAsString()`, `prev.getResponseCode()` |
| `sampler` | The current sampler (pre-processors) | `sampler.addArgument('a', 'b')` |
| `SampleResult` | The result of a JSR223 Sampler | `SampleResult.setResponseData(...)` |
| `AssertionResult` | The result of a JSR223 Assertion | `AssertionResult.setFailure(true)` |
| `log` | The JMeter log | `log.info('hello')` |
| `ctx` | The thread's context | `ctx.getThreadNum()` |

## The two golden rules

1. **Don't put `${...}` inside a script.** JMeter replaces it *before* Groovy compiles the code, which breaks caching and can inject odd values. Use `vars.get('name')` instead.
2. **Tick "Cache compiled script if available"** (it is on in every plan here) so the script is compiled once, not on every call.

## What plan 09 does

### 1. setUp Thread Group: get a token once and share it

A **setUp Thread Group** runs before all normal thread groups. It logs in as a service account and saves the token as a **property**:

```groovy
import groovy.json.JsonSlurper
def json = new JsonSlurper().parseText(prev.getResponseDataAsString())
props.put('sharedToken', json.token)
```

The main thread group then sends `Authorization: Bearer ${__P(sharedToken)}`.

This answers a common interview question: "How do you share a token across all threads?" Variables are per thread, so use a **property**, set in a setUp Thread Group. The alternative is for each thread to log in and extract its own token, which is more realistic when login is part of the load.

### 2. JSR223 Sampler: build dynamic test data

```groovy
def providerId = 'P' + (1001 + ThreadLocalRandom.current().nextInt(20))
def firstOfThisMonth = LocalDate.now().withDayOfMonth(1)
vars.put('from', firstOfThisMonth.minusMonths(1).toString())  // first day of last month
vars.put('to', firstOfThisMonth.minusDays(1).toString())      // last day of last month
SampleResult.setIgnore()   // keep this helper step out of the results
```

### 3. Post-processor and assertion: check the business numbers

A JSR223 PostProcessor reads `totalClaims` and `totalPaid` into variables, and a JSR223 Assertion fails the sample if there are no claims or the paid amount isn't positive.

### 4. Thread-level post-processor

A JSR223 PostProcessor placed directly under the Thread Group runs after **every** sampler, here counting reports per thread.

### 5. tearDown Thread Group

Runs after the test (also on a clean shutdown, because *Run tearDown Thread Groups after shutdown* is ticked on the Test Plan) and logs a summary line to `jmeter.log`.

## Run it

```powershell
jmeter -n -t test-plans/09_jsr223_groovy.jmx -l results/09.jtl -j results/09.log
python scripts/jtl_summary.py results/09.jtl
```

Open `results/09.log` and look for `setUp: shared token stored` and `tearDown: test finished`.

## Useful functions that run Groovy inline

- `${__groovy(...)}`: evaluate a Groovy expression inside any field (used for the workload mix in plan 10)
- `${__jexl3(...)}`: lighter expressions, good for If and While conditions

## Performance note

Every script runs for every sample on every thread. Keep scripts short, avoid heavy parsing of large responses during big load tests, and never call `Thread.sleep` in a script; use a timer.

**Next:** [10 · Non-GUI runs and the HTML dashboard](10-non-gui-runs-and-html-dashboard.md)
