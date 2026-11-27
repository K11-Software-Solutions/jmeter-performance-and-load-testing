# K11 Claims Analytics mock API

A small Node.js server (no dependencies, Node 18+) that the JMeter scripts in this repo test against. It is a **safe, local, legal** load-test target. All data is synthetic: no real members, providers or claims.

```powershell
node mock-server/server.js
```

## Settings

| Environment variable | Default | Effect |
|---|---|---|
| `PORT` | `3000` | Port to listen on |
| `POOL_SIZE` | `20` | Simulated database connections. Requests beyond this queue. |
| `QUEUE_TIMEOUT_MS` | `5000` | How long a request waits for a connection before it gets **503** |
| `LATENCY_FACTOR` | `1.0` | Multiplies all simulated work times (`10` = ten times slower) |
| `METRICS_LOG` | `0` | `1` prints pool and memory stats every 5 s |
| `LEAK` | `0` | `1` keeps ~10 KB per request in memory, to practise spotting a leak in a soak test |

PowerShell: `$env:POOL_SIZE=4; node mock-server/server.js` · Git Bash/macOS/Linux: `POOL_SIZE=4 node mock-server/server.js`

### The built-in bottleneck

Every API call "uses the database" for a while (login about 40 ms, dashboard about 60 ms, claims summary 120 ms + 15 ms per month in the range, all ±20%). Only `POOL_SIZE` calls can do that at the same time. The rest wait in a queue. That is how many real systems behave when a connection pool, thread pool or database is saturated:

- response times rise because of **queueing**, not because each request does more work,
- throughput **stops growing** at about `POOL_SIZE ÷ average work time`,
- after `QUEUE_TIMEOUT_MS`, requests fail with **503**.

`GET /metrics` shows the server side of the story (pool in use, queue length, 503 count, memory), so you can practise connecting JMeter results to server metrics.

## Users

`analyst01` … `analyst100`, all with the test-only password `learn-jmeter`. `locked_user` returns **423 Locked**.
Providers: `P1001` … `P1020`.

## Endpoints

### Health and metrics (no auth, not pooled)

| Method | Path | Returns |
|---|---|---|
| GET | `/health` | `{"status":"UP",...}` |
| GET | `/metrics` | Pool size, active, waiting, max queue seen, requests, 503s, 4xx, heap and RSS memory |

### JSON API

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/api/providers` | none | 20 synthetic providers |
| POST | `/api/auth/login` | none | Body `{"username","password"}` → `{"token","tokenType","expiresIn","user"}`; 401 bad credentials, 423 locked |
| GET | `/api/dashboard` | Bearer | Widgets and favourite providers |
| GET | `/api/reports/claims-summary?providerId=&from=&to=` | Bearer | Dates `YYYY-MM-DD`. Returns `reportId`, `totalClaims`, `totalPaid`, `byMonth`. 400 bad input, 404 unknown provider. Totals are the same for the same query. |
| POST | `/api/reports/claims-summary/export` | Bearer | Body `{"reportId"}` → **202** `{"exportId","status":"QUEUED"}` |
| GET | `/api/reports/exports/{exportId}` | Bearer | `QUEUED` → `RUNNING` → `READY` (about 1.5 s), then `downloadUrl` |
| GET | `/api/reports/exports/{exportId}/download` | Bearer | CSV file |

### HTML portal (cookies, CSRF token, form posts; good for recording and regex practice)

| Method | Path | Notes |
|---|---|---|
| GET | `/portal/login` | Sets a `SESSION` cookie; form has a hidden `_csrf` input |
| POST | `/portal/login` | Form `username`, `password`, `_csrf` → 302 to `/portal/home`; 403 if the CSRF token is wrong |
| GET | `/portal/home` | Welcome page with a report form |
| GET | `/portal/claims-summary?providerId=&from=&to=` | HTML report table |
| GET | `/portal/logout` | Ends the session |

## Quick check with curl

```bash
curl -s localhost:3000/health
TOKEN=$(curl -s -X POST localhost:3000/api/auth/login -H 'Content-Type: application/json' \
  -d '{"username":"analyst01","password":"learn-jmeter"}' | python -c "import sys,json;print(json.load(sys.stdin)['token'])")
curl -s "localhost:3000/api/reports/claims-summary?providerId=P1001&from=2026-01-01&to=2026-01-31" \
  -H "Authorization: Bearer $TOKEN"
```
