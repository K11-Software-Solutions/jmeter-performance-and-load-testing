# 13 · Backend Listener, InfluxDB and Grafana (optional)

> **Goal:** watch results live while a long test runs, instead of waiting for the HTML report at the end.
>
> **Script:** `test-plans/13_backend_listener_influxdb.jmx` · **Stack:** `observability/docker-compose.yml`
>
> **Status:** the `.jmx` file was run against the mock without InfluxDB (the test runs; the listener logs connection errors). The Docker stack and Grafana dashboard were **not** run while this repo was built, because Docker was not running on the build machine. Treat it as a starting point and check it on your machine.

## Why

The HTML report appears only after the test. In a 4-hour soak or a test watched by a team, you want live graphs, and you want them next to server metrics. The **Backend Listener** sends aggregated metrics every few seconds to a time-series database. Grafana draws them.

```
JMeter (Backend Listener) ──HTTP──► InfluxDB (database "jmeter") ◄── Grafana dashboards
```

## Start the stack

You need Docker Desktop (or Docker Engine) running.

```powershell
docker compose -f observability/docker-compose.yml up -d
```

- InfluxDB 1.8: `http://localhost:8086`, database `jmeter`
- Grafana: <http://localhost:3030>, with the *InfluxDB-JMeter* data source and the *K11 JMeter live results* dashboard pre-loaded (admin login `admin` / `admin`, for local learning only)

## Run the test

```powershell
jmeter -n -t test-plans/13_backend_listener_influxdb.jmx -Jusers=10 -Jduration=300 -l results/13.jtl
```

Open the Grafana dashboard while it runs.

## Backend Listener settings

| Parameter | Value | Meaning |
|---|---|---|
| Implementation | `InfluxdbBackendListenerClient` | Built into JMeter |
| `influxdbMetricsSender` | `HttpMetricsSender` | Sends over HTTP |
| `influxdbUrl` | `http://localhost:8086/write?db=jmeter` | Change with `-Jinfluxdb_url=...` |
| `application` | `k11-claims-mock` | A tag to tell projects apart |
| `measurement` | `jmeter` | The InfluxDB measurement name |
| `summaryOnly` | `false` | `false` = send per-label metrics, not only totals |
| `samplersRegex` | `.*` | Which labels to send |
| `percentiles` | `90;95;99` | Which percentiles to calculate |
| `testTitle`, `eventTags` | | Annotations for the start and end of the test |

For **InfluxDB 2.x**, use a URL like `http://host:8086/api/v2/write?org=my-org&bucket=jmeter` and add an `influxdbToken` parameter.

The listener sends *aggregated* data (counts, averages and percentiles per interval), not every sample, so it stays light. Keep writing the `.jtl` file as well: it is your complete record.

## What's in the starter dashboard

Four panels using InfluxQL against the fields the listener writes:

- active threads (`maxAT` where `transaction = 'internal'`)
- throughput (`count` where `transaction = 'all'`)
- p95 by transaction (`pct95.0`)
- errors per second (`countError`)

Community JMeter dashboards for this listener are also published on grafana.com. Search for "JMeter InfluxDB" and import one that matches your InfluxDB version.

## Stop and clean up

```powershell
docker compose -f observability/docker-compose.yml down        # keep data
docker compose -f observability/docker-compose.yml down -v     # also delete the data volume
```

**Next:** [14 · Reading results and finding bottlenecks](14-reading-results-and-finding-bottlenecks.md)
